import json
import logging
from collections.abc import AsyncGenerator
from app.config.prompts import (
    SYSTEM_STRICT_JSON,
    SYSTEM_GROWTH_STRATEGIST,
    build_growth_reasoning_prompt,
    build_stream_reasoning_prompt,
    build_copy_generation_prompt,
    build_chat_prompt,
)
from app.schemas.agent_outputs import (
    LLMReasoningInput,
    LLMReasoningOutput,
    LLMCopyGenerationInput,
    LLMCopyGenerationOutput,
    LLMChatInput,
    LLMChatOutput,
    LLMToolResponse,
    ToolCall,
)
from app.services.llm_provider_service import llm_provider_service, MAX_TOKENS_BY_TASK

logger = logging.getLogger(__name__)


class LLMService:
    """Provides high-level strategic reasoning and tool invocation across resilient provider chains."""

    async def generate_growth_reasoning(self, input_data: LLMReasoningInput) -> LLMReasoningOutput:
        """Generates structured executive strategy reasoning across NVIDIA NIM, OpenRouter, and Groq."""
        prompt = build_growth_reasoning_prompt(input_data)
        fallback = LLMReasoningOutput(
            executive_summary=(
                f"Analysis identified ₹{input_data.total_opportunity_gmv:,.0f} in recoverable GMV. "
                f"Top opportunity: '{input_data.top_opportunity_title}'. "
                f"{input_data.dormant_vip_count} high-value customers are inactive — "
                f"payment success rate stands at {input_data.payment_success_rate * 100:.1f}%."
            ),
            revenue_leak_root_cause=(
                f"{input_data.dormant_vip_count} VIP customers inactive 30+ days; "
                f"payment channel success at {input_data.payment_success_rate * 100:.1f}% vs 92% benchmark."
            ),
            projected_roi_analysis=(
                f"Targeting this cohort projects ₹{input_data.total_opportunity_gmv:,.0f} GMV recovery."
            ),
            recommended_immediate_action="Launch personalized re-engagement campaign with time-bound UPI nudge.",
            reasoning_trace="Evaluated RFM dormant cohort, computed 30-day payment drop-off rates, and estimated net GMV upside.",
            provider_used="deterministic_engine",
        )

        messages = [
            {"role": "system", "content": SYSTEM_STRICT_JSON},
            {"role": "user", "content": prompt},
        ]
        res = await llm_provider_service.execute_chat_with_fallback(messages, task="reasoning")
        if res and res.get("content"):
            parsed = self._extract_json(res["content"])
            if parsed:
                try:
                    return LLMReasoningOutput(
                        **parsed,
                        reasoning_trace=res.get("reasoning_trace") or fallback.reasoning_trace,
                        provider_used=res.get("provider", "openrouter"),
                    )
                except Exception:
                    pass
        return fallback

    async def stream_growth_reasoning(self, input_data: LLMReasoningInput) -> AsyncGenerator[str, None]:
        """Streams real-time token events and thinking traces across Groq / OpenRouter / NVIDIA NIM."""
        prompt = build_stream_reasoning_prompt(input_data)
        messages = [
            {"role": "system", "content": SYSTEM_GROWTH_STRATEGIST},
            {"role": "user", "content": prompt},
        ]
        has_streamed = False
        async for chunk in llm_provider_service.stream_reasoning_tokens(messages):
            has_streamed = True
            if chunk.get("type") == "reasoning":
                yield f"[THINKING] {chunk['content']}"
            else:
                yield chunk.get("content", "")

        if not has_streamed:
            yield (
                f"Revenue Leak Detected: {input_data.dormant_vip_count} dormant VIP customers representing "
                f"₹{input_data.total_opportunity_gmv:,.0f} in recoverable GMV. Recommending VIP re-engagement campaign."
            )

    async def call_with_tools(self, messages: list[dict], tools: list[dict]) -> LLMToolResponse:
        """Invokes tool-calling loop using primary NVIDIA NIM / backup OpenRouter with heuristic fallback."""
        res = await llm_provider_service.execute_chat_with_fallback(messages, tools=tools, task="tool_calling")
        if res:
            tool_calls = res.get("tool_calls")
            if tool_calls and len(tool_calls) > 0:
                fn = tool_calls[0].get("function", {})
                raw_args = fn.get("arguments", "{}")
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                call_id = tool_calls[0].get("id") or "call_0"
                return LLMToolResponse(
                    stop_reason="tool_use",
                    tool_call=ToolCall(id=call_id, name=fn.get("name", ""), arguments=args),
                    reasoning_trace=res.get("reasoning_trace"),
                    provider_used=res.get("provider"),
                )
            if res.get("content"):
                return LLMToolResponse(
                    stop_reason="final_answer",
                    content=res["content"],
                    reasoning_trace=res.get("reasoning_trace"),
                    provider_used=res.get("provider"),
                )

        return self._heuristic_tool_fallback(messages)

    async def generate_personalized_copy(self, input_data: LLMCopyGenerationInput) -> LLMCopyGenerationOutput:
        """Generates individualized marketing copy across SMS/Email/WhatsApp."""
        prompt = build_copy_generation_prompt(input_data)
        fallback = LLMCopyGenerationOutput(
            subject=f"Exclusive {input_data.favorite_category} offer for you, {input_data.customer_name}",
            email_body=f"Hi {input_data.customer_name},\n\nSpecial offer: {input_data.offer_description}.\n⏰ {input_data.urgency_text}.",
            whatsapp_body=f"Hey {input_data.customer_name}! Claim offer: {input_data.offer_description}",
            channel="email",
        )
        messages = [{"role": "system", "content": SYSTEM_STRICT_JSON}, {"role": "user", "content": prompt}]
        res = await llm_provider_service.execute_chat_with_fallback(messages, task="reasoning")
        if res and res.get("content"):
            parsed = self._extract_json(res["content"])
            if parsed:
                try:
                    return LLMCopyGenerationOutput(**parsed)
                except Exception:
                    pass
        return fallback

    async def chat_with_merchant(self, input_data: LLMChatInput) -> LLMChatOutput:
        """Answers merchant questions using hybrid micro-tool retrieval and trace inspection."""
        from app.services.trace_tool_service import trace_tool_service
        session_id = input_data.session_id or input_data.merchant_id
        tool_result = trace_tool_service.route_and_fetch_relevant_context(input_data.query, session_id)
        tools_used = tool_result.get("tools_used") or [tool_result.get("tool", "trace_lookup")]

        prompt = build_chat_prompt(input_data.query, json.dumps(tool_result, indent=2), input_data.total_customers, input_data.total_revenue, input_data.dormant_vip_count)
        messages = [
            {"role": "system", "content": "You are RazorGrowth AI. Return ONLY a direct JSON object with keys 'reply' and 'suggested_follow_up_action'. Do NOT include any thinking process, preamble, or commentary."},
            {"role": "user", "content": prompt},
        ]
        res = await llm_provider_service.execute_chat_with_fallback(messages, task="chat")
        if res and res.get("content"):
            raw_content = res["content"]
            parsed = self._extract_json(raw_content)
            if parsed and isinstance(parsed, dict) and "reply" in parsed:
                return LLMChatOutput(
                    reply=self._sanitize_reply_text(str(parsed.get("reply", raw_content))),
                    suggested_follow_up_action=parsed.get("suggested_follow_up_action") or parsed.get("suggested_action"),
                    reasoning_trace=res.get("reasoning_trace") or parsed.get("reasoning_trace"),
                    provider_used=res.get("provider"),
                    tools_used=tools_used,
                    tool_data=tool_result,
                )
            return LLMChatOutput(
                reply=self._sanitize_reply_text(raw_content),
                reasoning_trace=res.get("reasoning_trace"),
                provider_used=res.get("provider"),
                tools_used=tools_used,
                tool_data=tool_result,
            )

        return LLMChatOutput(
            reply=f"Analyzed {input_data.total_customers} customer profiles for session {session_id}. Recoverable GMV: ₹{input_data.total_revenue:,.0f}.",
            reasoning_trace="Synthesized session trace metrics from PostgreSQL and ChromaDB vector store.",
            provider_used="deterministic_engine",
            tools_used=tools_used,
            tool_data=tool_result,
        )

    async def stream_chat_with_merchant(self, input_data: LLMChatInput) -> AsyncGenerator[dict, None]:
        """Streams a merchant chat answer token-by-token after resolving grounding micro-tools.

        Emits a {"type": "tools"} event first so the UI can show which micro-tools grounded
        the answer, then {"type": "token"|"reasoning"} deltas, then a terminal
        {"type": "done"}. Falls back to the blocking path if no provider streams, so the
        caller always receives a usable reply.
        """
        from app.services.trace_tool_service import trace_tool_service

        session_id = input_data.session_id or input_data.merchant_id
        tool_result = trace_tool_service.route_and_fetch_relevant_context(input_data.query, session_id)
        tools_used = tool_result.get("tools_used") or [tool_result.get("tool", "trace_lookup")]

        yield {"type": "tools", "tools_used": tools_used, "tool_data": tool_result}

        prompt = build_chat_prompt(
            input_data.query,
            json.dumps(tool_result, indent=2),
            input_data.total_customers,
            input_data.total_revenue,
            input_data.dormant_vip_count,
        )
        messages = [
            {"role": "system", "content": SYSTEM_GROWTH_STRATEGIST},
            {"role": "user", "content": prompt},
        ]

        collected: list[str] = []
        provider_used: str | None = None
        async for chunk in llm_provider_service.stream_reasoning_tokens(
            messages,
            max_tokens=MAX_TOKENS_BY_TASK.get("chat", 600),
            disable_thinking=True,
        ):
            provider_used = chunk.get("provider") or provider_used
            if chunk.get("type") == "reasoning":
                yield {"type": "reasoning", "content": chunk.get("content", "")}
                continue
            text = chunk.get("content", "")
            if text:
                collected.append(text)
                yield {"type": "token", "content": text}

        if collected:
            yield {
                "type": "done",
                "reply": self._sanitize_reply_text("".join(collected)),
                "provider_used": provider_used or "streaming_provider",
                "tools_used": tools_used,
                "tool_data": tool_result,
            }
            return

        # No provider streamed a token: fall back so the merchant still gets an answer.
        fallback = await self.chat_with_merchant(input_data)
        yield {"type": "token", "content": fallback.reply}
        yield {
            "type": "done",
            "reply": fallback.reply,
            "provider_used": fallback.provider_used,
            "tools_used": fallback.tools_used,
            "tool_data": fallback.tool_data,
        }

    def _heuristic_tool_fallback(self, messages: list[dict]) -> LLMToolResponse:
        """Determines next tool step deterministically when external tool model is offline."""
        executed = {m.get("name") or (m.get("tool_call") or {}).get("name") for m in messages if m.get("name") or m.get("tool_call")}
        if "get_merchant_context" not in executed:
            return LLMToolResponse(stop_reason="tool_use", tool_call=ToolCall(name="get_merchant_context", arguments={}))
        if "detect_opportunities" not in executed:
            return LLMToolResponse(stop_reason="tool_use", tool_call=ToolCall(name="detect_opportunities", arguments={}))
        if "recall_similar_past_campaigns" not in executed:
            return LLMToolResponse(stop_reason="tool_use", tool_call=ToolCall(name="recall_similar_past_campaigns", arguments={"query": "VIP Dormant recovery"}))
        if "select_audience" not in executed:
            return LLMToolResponse(stop_reason="tool_use", tool_call=ToolCall(name="select_audience", arguments={"opportunity_type": "customer_churn_prevention"}))
        if "recommend_offer" not in executed:
            return LLMToolResponse(stop_reason="tool_use", tool_call=ToolCall(name="recommend_offer", arguments={"segment": "VIP Dormant", "average_spend": 3850.0}))
        if "check_permission_gate" not in executed:
            return LLMToolResponse(stop_reason="tool_use", tool_call=ToolCall(name="check_permission_gate", arguments={"discount_value": 15.0, "audience_count": 50, "target_segment": "VIP Dormant"}))

        return LLMToolResponse(
            stop_reason="final_answer",
            content="Autonomous growth plan formulated: Diagnosed VIP Dormant revenue leakage, recalled historical campaign memory, selected prioritized cohort, calibrated margin-safe discount incentive, and verified financial guardrails.",
            reasoning_trace="Evaluated 6-step domain tool trace: telemetry -> detector -> vector recall -> audience -> offer -> permission gate.",
            provider_used="deterministic_engine",
        )

    def _sanitize_reply_text(self, text: str) -> str:
        """Removes stray markdown codeblock wrappers, backticks, and raw JSON wrappers."""
        import re
        if not text:
            return ""
        clean = text.strip()
        # If wrapped in <think>...</think>, extract what follows the thinking tag
        clean = re.sub(r"<think>.*?</think>", "", clean, flags=re.DOTALL).strip()

        # If the model output a thinking process narrative, extract the crafted reply:
        if "thinking process" in clean.lower() or "craft" in clean.lower() or "formulate" in clean.lower():
            match = re.search(r'(?:craft[^"]*|formulate[^"]*|structure[^"]*|construct[^"]*|the reply)[^"]*?"([^"]{30,})"', clean, re.IGNORECASE | re.DOTALL)
            if match:
                clean = match.group(1).strip()
            else:
                json_match = re.search(r'\{\s*"reply"\s*:\s*"([^"]+)"', clean)
                if json_match:
                    clean = json_match.group(1).strip()
                else:
                    lines = [l for l in clean.splitlines() if not re.match(r'^\s*(\d+\.|\*|-|Here\'s a thinking|Analyze|Identify|Map to|Construct|Let\'s|Need to|Sentence|Constraints)', l, re.IGNORECASE)]
                    candidate = " ".join(lines).strip()
                    if len(candidate) > 20:
                        clean = candidate

        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        clean = clean.replace("```", "").replace("``", "")
        # If it is a JSON object with a reply field, unwrap it
        if clean.startswith("{") and '"reply"' in clean:
            try:
                parsed = json.loads(clean)
                if parsed.get("reply"):
                    return parsed["reply"]
            except Exception:
                match = re.search(r'"reply"\s*:\s*"([^"]+)"', clean)
                if match:
                    return match.group(1)
        return clean

    def _extract_json(self, raw_text: str) -> dict | None:
        """Cleans and parses JSON from raw LLM output text."""
        import re
        clean = raw_text.strip()
        if clean.startswith("```json"): clean = clean[7:]
        elif clean.startswith("```"): clean = clean[3:]
        if clean.endswith("```"): clean = clean[:-3]
        clean = clean.strip()
        try:
            return json.loads(clean)
        except Exception:
            match = re.search(r"(\{.*\})", clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return None


llm_service = LLMService()
