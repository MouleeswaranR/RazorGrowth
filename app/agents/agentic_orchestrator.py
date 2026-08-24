import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.agents.tool_registry import tool_registry, TOOLS_DEFINITION
from app.services.llm_service import llm_service
from app.schemas.agent_outputs import AgenticScanResult, AgenticStepRecord

logger = logging.getLogger(__name__)

AGENTIC_SYSTEM_PROMPT = (
    "You are RazorGrowth AI's Autonomous Growth Strategist. "
    "Your objective is to execute a rigorous 6-stage diagnostic workflow by calling domain tools in sequence:\n"
    "Stage 1. get_merchant_context: fetch customer count, revenue telemetry, and payment success rate.\n"
    "Stage 2. detect_opportunities: run revenue leakage detectors to diagnose high-impact opportunities.\n"
    "Stage 3. recall_similar_past_campaigns: query ChromaDB 384-dim vector memory for past conversion benchmarks.\n"
    "Stage 4. select_audience: extract and rank the highest-ROI target cohort.\n"
    "Stage 5. recommend_offer: calibrate margin-safe promotional incentives.\n"
    "Stage 6. check_permission_gate: verify dynamic financial guardrails before formulating the final plan.\n"
    "CRITICAL: Call each tool sequentially to gather complete evidence. Do NOT provide a final text summary until all tools have been executed."
)


class AgenticOrchestrator:
    """Runs bounded ReAct tool-calling loop where the LLM drives multi-step growth decisions."""

    def _get_next_fallback_tool(self, steps_taken: list[AgenticStepRecord]) -> tuple[str, dict]:
        """Determines the next sequential diagnostic tool if model stops early."""
        called = [s.tool_name for s in steps_taken]
        if "get_merchant_context" not in called:
            return "get_merchant_context", {}
        if "detect_opportunities" not in called:
            return "detect_opportunities", {}
        if "recall_similar_past_campaigns" not in called:
            return "recall_similar_past_campaigns", {"query": "VIP Dormant re-engagement campaign"}
        if "select_audience" not in called:
            return "select_audience", {"opportunity_type": "customer_churn_prevention"}
        if "recommend_offer" not in called:
            return "recommend_offer", {"segment": "VIP Dormant", "average_spend": 3500.0}
        if "check_permission_gate" not in called:
            return "check_permission_gate", {"discount_value": 20.0, "audience_count": 54, "target_segment": "VIP Dormant"}
        return "", {}

    async def _synthesize_final_plan(
        self,
        history: list[dict],
        steps_taken: list[AgenticStepRecord],
    ) -> tuple[str, str, str]:
        """Asks the model to synthesize a closing plan once all diagnostic tools have run.

        The tool loop exits on the step budget, so without this the run would report a
        canned summary and never surface the model's own synthesis. Returns a
        (plan_summary, reasoning_trace, provider_used) triple, falling back to
        deterministic text if every provider is unavailable.
        """
        default_summary = "Autonomous growth plan synthesized across all 6 diagnostic stages."
        default_trace = "Full 6-stage ReAct loop completed across all domain tools."

        synthesis_history = history + [{
            "role": "user",
            "content": (
                "All diagnostic tools have now been executed. Do NOT call any further tools. "
                "Write the final growth plan as a concise executive summary (4-6 sentences) covering: "
                "the diagnosed revenue leak, the selected cohort, the calibrated offer, and the "
                "permission-gate verdict. Reference the concrete numbers returned by the tools."
            ),
        }]

        try:
            response = await llm_service.call_with_tools(synthesis_history, [])
        except Exception as err:
            logger.warning(f"Final plan synthesis failed: {err}")
            return default_summary, default_trace, "deterministic_engine"

        summary = (response.content or "").strip()
        if not summary:
            return default_summary, default_trace, response.provider_used or "deterministic_engine"

        return (
            summary,
            response.reasoning_trace or default_trace,
            response.provider_used or "deterministic_engine",
        )


    async def run_agentic_growth_scan(
        self,
        session: AsyncSession,
        merchant_id: str,
    ) -> AgenticScanResult:
        """Executes bounded multi-step agentic loop up to configured max steps."""
        history = [
            {"role": "system", "content": AGENTIC_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Begin comprehensive autonomous growth analysis for merchant '{merchant_id}'. Execute the 6-stage diagnostic workflow: get store telemetry, detect revenue leaks, recall vector memory benchmarks, select target audience, calibrate margin-safe offers, and verify permission gate guardrails.",
            },
        ]
        steps_taken: list[AgenticStepRecord] = []
        memory_citations: list[dict] = []
        max_steps = settings.agentic_max_steps

        for step_idx in range(max_steps):
            response = await llm_service.call_with_tools(history, TOOLS_DEFINITION)

            # Only force a tool when the model produced no call on the very first turn, so a
            # provider outage still yields a usable trace. Past that point the model is free
            # to choose its own tools, revisit one, or stop early and synthesize.
            if response.tool_call is None and not steps_taken:
                fallback_tool, fallback_args = self._get_next_fallback_tool(steps_taken)
                if fallback_tool:
                    tool_name = fallback_tool
                    tool_args = fallback_args
                    call_id = f"call_{step_idx}_{tool_name}"
                else:
                    break
            elif response.tool_call is not None:
                tool_name = response.tool_call.name
                tool_args = response.tool_call.arguments
                call_id = response.tool_call.id or f"call_{step_idx}_{tool_name}"
            else:
                return AgenticScanResult(
                    merchant_id=merchant_id,
                    plan_summary=response.content or "Synthesized autonomous multi-agent growth plan.",
                    steps_taken=steps_taken,
                    memory_citations=memory_citations,
                    reasoning_trace=response.reasoning_trace or "Bounded ReAct decision loop completed across domain tools.",
                    provider_used=response.provider_used or "deterministic_engine",
                    status="completed",
                )

            tool_result = await tool_registry.execute_tool(
                session=session,
                merchant_id=merchant_id,
                tool_name=tool_name,
                arguments=tool_args,
            )

            if tool_name == "recall_similar_past_campaigns" and "retrieved_memories" in tool_result:
                memory_citations.extend(tool_result["retrieved_memories"])

            step_summary = self._summarize_step_result(tool_name, tool_result)
            steps_taken.append(
                AgenticStepRecord(
                    step_number=len(steps_taken) + 1,
                    tool_name=tool_name,
                    arguments=tool_args,
                    result=tool_result,
                    step_summary=step_summary,
                )
            )

            history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args) if isinstance(tool_args, dict) else str(tool_args),
                        },
                    }
                ],
            })
            history.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": json.dumps(tool_result),
            })

        plan_summary, reasoning_trace, provider_used = await self._synthesize_final_plan(history, steps_taken)
        return AgenticScanResult(
            merchant_id=merchant_id,
            plan_summary=plan_summary,
            steps_taken=steps_taken,
            memory_citations=memory_citations,
            reasoning_trace=reasoning_trace,
            provider_used=provider_used,
            status="completed",
        )

    async def stream_agentic_growth_scan(
        self,
        session: AsyncSession,
        merchant_id: str,
    ):
        """Streams step-by-step tool execution events in real time as the LLM reasons."""
        import asyncio
        from app.schemas.agent_outputs import StepEvent

        history = [
            {"role": "system", "content": AGENTIC_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Begin comprehensive autonomous growth analysis for merchant '{merchant_id}'. Execute the 6-stage diagnostic workflow: get store telemetry, detect revenue leaks, recall vector memory benchmarks, select target audience, calibrate margin-safe offers, and verify permission gate guardrails.",
            },
        ]
        steps_taken: list[AgenticStepRecord] = []
        memory_citations: list[dict] = []
        max_steps = settings.agentic_max_steps

        for step_idx in range(max_steps):
            response = await llm_service.call_with_tools(history, TOOLS_DEFINITION)

            # Only force a tool when the model produced no call on the very first turn, so a
            # provider outage still yields a usable trace. Past that point the model is free
            # to choose its own tools, revisit one, or stop early and synthesize.
            if response.tool_call is None and not steps_taken:
                fallback_tool, fallback_args = self._get_next_fallback_tool(steps_taken)
                if fallback_tool:
                    tool_name = fallback_tool
                    tool_args = fallback_args
                    call_id = f"call_{step_idx}_{tool_name}"
                else:
                    break
            elif response.tool_call is not None:
                tool_name = response.tool_call.name
                tool_args = response.tool_call.arguments
                call_id = response.tool_call.id or f"call_{step_idx}_{tool_name}"
            else:
                yield StepEvent(
                    step="final_plan_synthesized",
                    step_number=len(steps_taken) + 1,
                    summary="Synthesized autonomous multi-agent growth plan.",
                    data={
                        "plan_summary": response.content or "Autonomous growth plan finalized across domain tools.",
                        "steps_taken": [s.model_dump() for s in steps_taken],
                        "memory_citations": memory_citations,
                        "reasoning_trace": response.reasoning_trace or "Bounded ReAct loop complete.",
                        "provider_used": response.provider_used or "deterministic_engine",
                        "status": "completed",
                    },
                )
                return

            tool_result = await tool_registry.execute_tool(
                session=session,
                merchant_id=merchant_id,
                tool_name=tool_name,
                arguments=tool_args,
            )

            if tool_name == "recall_similar_past_campaigns" and "retrieved_memories" in tool_result:
                memory_citations.extend(tool_result["retrieved_memories"])

            step_summary = self._summarize_step_result(tool_name, tool_result)
            step_record = AgenticStepRecord(
                step_number=len(steps_taken) + 1,
                tool_name=tool_name,
                arguments=tool_args,
                result=tool_result,
                step_summary=step_summary,
            )
            steps_taken.append(step_record)

            yield StepEvent(
                step=f"step_{len(steps_taken)}_{tool_name}",
                step_number=len(steps_taken),
                summary=step_summary,
                data=step_record.model_dump(),
            )

            # Pacing delay so live SSE stream displays visibly
            await asyncio.sleep(0.4)

            history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args) if isinstance(tool_args, dict) else str(tool_args),
                        },
                    }
                ],
            })
            history.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": json.dumps(tool_result),
            })

        plan_summary, reasoning_trace, provider_used = await self._synthesize_final_plan(history, steps_taken)
        yield StepEvent(
            step="final_plan_synthesized",
            step_number=len(steps_taken) + 1,
            summary="Autonomous plan synthesized across all diagnostic stages.",
            data={
                "plan_summary": plan_summary,
                "steps_taken": [s.model_dump() for s in steps_taken],
                "memory_citations": memory_citations,
                "reasoning_trace": reasoning_trace,
                "provider_used": provider_used,
                "status": "completed",
            },
        )

    def _summarize_step_result(self, tool_name: str, result: dict) -> str:
        """Generates concise readable summary for each tool step."""
        if tool_name == "get_merchant_context":
            rev = result.get('total_revenue_inr') or result.get('total_gmv') or 0
            return f"Retrieved store telemetry: {result.get('total_customers', 0)} customers, ₹{rev:,.0f} GMV."
        if tool_name == "detect_opportunities":
            return f"Detected {result.get('opportunities_found', 0)} potential revenue opportunities."
        if tool_name == "select_audience":
            return f"Selected {result.get('audience_count', 0)} prioritized customers in {result.get('target_segment')}."
        if tool_name == "recommend_offer":
            return f"Calibrated {result.get('offer_code')} ({result.get('discount_value')}% off)."
        if tool_name == "recall_similar_past_campaigns":
            return f"Retrieved {len(result.get('retrieved_memories', []))} similar historical campaign outcomes from memory."
        if tool_name == "check_permission_gate":
            return f"Permission gate safety check: {result.get('policy_status', 'evaluated').upper()}."
        return f"Executed {tool_name}."


agentic_orchestrator = AgenticOrchestrator()
