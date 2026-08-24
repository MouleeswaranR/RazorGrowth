"""
Script to test tool-calling across all configured LLM providers (NVIDIA NIM, OpenRouter, Groq, Mistral)
using API keys from the root .env file.
"""

import os
import json
import time
import httpx
from dotenv import load_dotenv

# Load .env from root
load_dotenv()

# Simple Tool Definition
TOOL_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "calculate_merchant_discount",
            "description": "Calculates the recommended margin-safe discount percentage for a merchant customer segment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_segment": {
                        "type": "string",
                        "description": "Target segment: 'VIP Dormant', 'Loyal At Risk', 'New Customer'",
                    },
                    "average_order_value": {
                        "type": "number",
                        "description": "Average purchase amount in INR",
                    },
                    "target_margin_preserve_pct": {
                        "type": "number",
                        "description": "Minimum margin percentage to preserve (e.g. 20.0)",
                    },
                },
                "required": ["customer_segment", "average_order_value"],
            },
        },
    }
]

PROMPT_MESSAGES = [
    {
        "role": "system",
        "content": "You are RazorGrowth AI's Autonomous Strategist. You MUST call the calculate_merchant_discount tool to determine the incentive.",
    },
    {
        "role": "user",
        "content": "A merchant has 50 customers in 'VIP Dormant' with an average order value of 3500 INR. Call the calculate_merchant_discount tool now.",
    },
]

PROVIDERS = [
    {
        "name": "NVIDIA NIM",
        "base_url": os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        "api_key": os.getenv("NVIDIA_NIM_API_KEY", ""),
        "model": os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
        "headers": {},
    },
    {
        "name": "OpenRouter",
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "model": os.getenv("AGENTIC_MODEL_NAME", os.getenv("AI_MODEL_NAME", "nvidia/nemotron-3-ultra-550b-a55b:free")),
        "headers": {
            "HTTP-Referer": "https://razorgrowth.ai",
            "X-Title": "RazorGrowth AI",
        },
    },
    {
        "name": "Groq",
        "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "headers": {},
    },
    {
        "name": "Mistral AI",
        "base_url": os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
        "api_key": os.getenv("MISTRAL_API_KEY", ""),
        "model": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
        "headers": {},
    },
]


def test_provider(provider: dict):
    name = provider["name"]
    api_key = provider["api_key"].strip()
    base_url = provider["base_url"].rstrip("/")
    model = provider["model"]

    print(f"\n{'='*60}")
    print(f"Testing Provider: {name}")
    print(f"Base URL: {base_url}")
    print(f"Model:    {model}")

    if not api_key or api_key.startswith("your-") or "your_" in api_key:
        print(f"Status:   [SKIPPED] No valid API key configured in .env")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        **provider.get("headers", {}),
    }

    payload = {
        "model": model,
        "messages": PROMPT_MESSAGES,
        "tools": TOOL_DEFINITION,
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    start_time = time.time()
    endpoint = f"{base_url}/chat/completions"

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
            latency = round((time.time() - start_time) * 1000, 1)

            if resp.status_code == 200:
                data = resp.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                tool_calls = message.get("tool_calls", [])
                reasoning = message.get("reasoning_content") or message.get("reasoning")
                content = message.get("content")

                print(f"Status:   [SUCCESS] HTTP 200 (Latency: {latency}ms)")

                if tool_calls:
                    print(f"Tool:     SUCCESSFULLY INVOKED ({len(tool_calls)} call(s))")
                    for tc in tool_calls:
                        fn_name = tc.get("function", {}).get("name")
                        fn_args = tc.get("function", {}).get("arguments")
                        print(f"  -> Tool Name: {fn_name}")
                        print(f"  -> Arguments: {fn_args}")
                elif content:
                    print(f"Response: {content[:200]}...")
                
                if reasoning:
                    print(f"Reasoning Trace: {reasoning[:200]}...")
            else:
                print(f"Status:   [FAILED] HTTP {resp.status_code} (Latency: {latency}ms)")
                print(f"Error:    {resp.text[:300]}")
    except Exception as exc:
        print(f"Status:   [ERROR] Connection failed: {exc}")


def main():
    print("RazorGrowth AI - Multi-Provider Tool Calling Test Suite")
    print("Reading environment keys from .env...")
    for p in PROVIDERS:
        test_provider(p)
    print(f"\n{'='*60}\nDone.")


if __name__ == "__main__":
    main()
