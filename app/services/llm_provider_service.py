import json
import logging
import re
from typing import AsyncGenerator
from dataclasses import dataclass
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 1024

# These models are reasoning models: a larger completion budget is spent on hidden
# <think> tokens, so an oversized cap costs wall-clock without improving the answer.
# Measured on nemotron-3-super-120b (3 runs each, same chat prompt):
#   2048 -> 9.99s | 800 -> 7.83s | 600 -> 6.13s (no truncation) | 400 -> 4.03s but
#   truncated 2 of 3 responses. 600 is the fastest budget that never truncates.
# Tool calls emit a tiny function payload and are left at the benchmarked 1024, where
# tool-selection accuracy measured 100%.
MAX_TOKENS_BY_TASK = {
    "chat": 600,
    "tool_calling": DEFAULT_MAX_TOKENS,
    "reasoning": DEFAULT_MAX_TOKENS,
}


@dataclass
class ProviderEndpoint:
    """Encapsulates API connection attributes for an LLM provider."""
    name: str
    base_url: str
    api_key: str
    model: str
    fallback_models: tuple[str, ...] = ()

    def model_chain(self) -> list[str]:
        """Returns the tier-1 model followed by its configured fallbacks, de-duplicated."""
        chain: list[str] = []
        for candidate in (self.model, *self.fallback_models):
            if candidate and candidate not in chain:
                chain.append(candidate)
        return chain

    def is_configured(self) -> bool:
        """Checks if provider has valid non-placeholder API key."""
        if not self.api_key or not self.api_key.strip():
            return False
        key = self.api_key.lower()
        return not any(p in key for p in ["your-", "your_", "placeholder", "here", "sk-your", "gsk_your", "nvapi_your"])

    def get_headers(self) -> dict[str, str]:
        """Constructs authorization headers for HTTP requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.name == "openrouter":
            headers["HTTP-Referer"] = "https://razorgrowth.ai"
            headers["X-Title"] = "RazorGrowth AI"
        return headers


class LLMProviderService:
    """Manages multi-provider failover across NVIDIA NIM, OpenRouter, Groq, and Mistral."""

    def __init__(self) -> None:
        """Initializes provider endpoints and their benchmarked model fallback tiers."""
        self._endpoints = {
            "nvidia_nim": ProviderEndpoint(
                "nvidia_nim",
                settings.nvidia_nim_base_url,
                settings.nvidia_nim_api_key,
                settings.nvidia_nim_model,
                (settings.nvidia_nim_model_fallback_2, settings.nvidia_nim_model_fallback_3),
            ),
            "openrouter": ProviderEndpoint(
                "openrouter",
                settings.openrouter_base_url,
                settings.openrouter_api_key,
                settings.agentic_model_name,
                (settings.openrouter_model_fallback_2, settings.openrouter_model_fallback_3),
            ),
            "groq": ProviderEndpoint("groq", settings.groq_base_url, settings.groq_api_key, settings.groq_model),
            "mistral": ProviderEndpoint("mistral", settings.mistral_base_url, settings.mistral_api_key, settings.mistral_model),
        }

    def get_chain_for_task(self, task: str = "reasoning") -> list[ProviderEndpoint]:
        """Returns prioritized provider chain based on task characteristics."""
        if task == "streaming":
            order = ["groq", "openrouter", "nvidia_nim", "mistral"]
        elif task == "tool_calling":
            order = ["nvidia_nim", "openrouter", "groq", "mistral"]
        else:
            order = ["nvidia_nim", "openrouter", "groq", "mistral"]

        configured = [self._endpoints[k] for k in order if self._endpoints[k].is_configured()]
        if not configured:
            # Fall back to openrouter even if placeholder for consistent mock routing
            return [self._endpoints["openrouter"]]
        return configured

    async def execute_chat_with_fallback(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        task: str = "reasoning",
        timeout: float = 60.0,
        max_tokens: int | None = None,
    ) -> dict | None:
        """Executes completion across provider chain with automatic intra-provider model fallbacks."""
        chain = self.get_chain_for_task(task)
        token_budget = max_tokens or MAX_TOKENS_BY_TASK.get(task, DEFAULT_MAX_TOKENS)
        for provider in chain:
            for model_name in provider.model_chain():
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": token_budget,
                }
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        resp = await client.post(
                            f"{provider.base_url.rstrip('/')}/chat/completions",
                            headers=provider.get_headers(),
                            json=payload,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            result = self._parse_provider_response(data, provider.name)
                            return result
                        logger.warning(f"Provider '{provider.name}' ({model_name}) returned status {resp.status_code}: {resp.text[:120]}")
                except Exception as err:
                    err_name = str(err) or type(err).__name__
                    logger.warning(f"Provider '{provider.name}' ({model_name}) request failed: {err_name}")

        return None

    def _parse_provider_response(self, data: dict, provider_name: str) -> dict:
        """Extracts content, tool calls, and model reasoning trace from raw provider response."""
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "") or ""
        tool_calls = msg.get("tool_calls")
        
        # Extract reasoning from multiple possible locations
        reasoning_trace = None
        
        # 1. Check for reasoning_content field (some models)
        if msg.get("reasoning_content"):
            reasoning_trace = msg.get("reasoning_content")
        
        # 2. Check for reasoning parameter (DeepSeek R1 style)
        elif msg.get("reasoning"):
            reasoning_trace = msg.get("reasoning")
        
        # 3. Extract <think>...</think> tags from content
        elif "<think>" in content and "</think>" in content:
            match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
            if match:
                reasoning_trace = match.group(1).strip()
                # Remove think tags from main content
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return {
            "provider": provider_name,
            "content": content,
            "tool_calls": tool_calls,
            "reasoning_trace": reasoning_trace,
        }

    async def stream_reasoning_tokens(
        self,
        messages: list[dict],
        timeout: float = 60.0,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        disable_thinking: bool = False,
    ) -> AsyncGenerator[dict, None]:
        """Streams real-time token events and thinking traces across fallback provider chain."""
        chain = self.get_chain_for_task("streaming")
        for provider in chain:
            for model_name in provider.model_chain():
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                if disable_thinking:
                    # Nemotron-family reasoning models buffer a long hidden <think> phase
                    # before the first visible token, which ruins time-to-first-token for
                    # interactive chat. Providers ignore unknown keys, so this stays safe.
                    payload["chat_template_kwargs"] = {"thinking": False}
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        async with client.stream(
                            "POST",
                            f"{provider.base_url.rstrip('/')}/chat/completions",
                            headers=provider.get_headers(),
                            json=payload,
                        ) as stream:
                            if stream.status_code == 200:
                                async for raw_line in stream.aiter_lines():
                                    if not raw_line.startswith("data: "):
                                        continue
                                    chunk_str = raw_line[6:].strip()
                                    if chunk_str == "[DONE]":
                                        break
                                    try:
                                        chunk_data = json.loads(chunk_str)
                                        delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                        if "reasoning_content" in delta:
                                            yield {"type": "reasoning", "content": delta["reasoning_content"], "provider": provider.name, "model": model_name}
                                        elif "content" in delta and delta["content"]:
                                            yield {"type": "token", "content": delta["content"], "provider": provider.name, "model": model_name}
                                    except Exception:
                                        continue
                                return
                except Exception as err:
                    err_name = str(err) or type(err).__name__
                    logger.warning(f"Streaming failed for provider '{provider.name}' ({model_name}): {err_name}")


llm_provider_service = LLMProviderService()
