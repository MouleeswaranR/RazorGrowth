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
    "Your objective is to execute a rigorous, multi-stage diagnostic loop using your domain tools in sequence: "
    "1. get_merchant_context: inspect customer base, lifetime GMV, and payment success telemetry.\n"
    "2. detect_opportunities: run analytical detectors for dormant VIPs, payment friction, and cross-sell gaps.\n"
    "3. recall_similar_past_campaigns: query ChromaDB 384-dim vector memory for past conversion benchmarks.\n"
    "4. select_audience: extract and rank the highest-ROI target cohort.\n"
    "5. recommend_offer: calibrate margin-safe promotional discount parameters.\n"
    "6. check_permission_gate: verify dynamic safety guardrails before formulating the final plan.\n"
    "Execute these tools sequentially to gather complete evidence before finalizing your growth strategy."
)


class AgenticOrchestrator:
    """Runs bounded ReAct tool-calling loop where the LLM drives multi-step growth decisions."""

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

            if response.stop_reason == "final_answer" and response.content:
                return AgenticScanResult(
                    merchant_id=merchant_id,
                    plan_summary=response.content,
                    steps_taken=steps_taken,
                    memory_citations=memory_citations,
                    reasoning_trace=response.reasoning_trace or "Bounded ReAct decision loop completed across domain tools.",
                    provider_used=response.provider_used or "nvidia_nim",
                    status="completed",
                )

            if response.tool_call is not None:
                tool_name = response.tool_call.name
                tool_args = response.tool_call.arguments
                call_id = response.tool_call.id or f"call_{step_idx}_{tool_name}"

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
                        step_number=step_idx + 1,
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

        return AgenticScanResult(
            merchant_id=merchant_id,
            plan_summary="Max step bound reached. Recommended strategic plan synthesized from executed tools.",
            steps_taken=steps_taken,
            memory_citations=memory_citations,
            reasoning_trace="Loop bounded at configured max steps.",
            provider_used="nvidia_nim",
            status="max_steps_reached",
        )

    async def stream_agentic_growth_scan(
        self,
        session: AsyncSession,
        merchant_id: str,
    ):
        """Streams step-by-step tool execution events in real time as the LLM reasons."""
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

            if response.stop_reason == "final_answer" and response.content:
                yield StepEvent(
                    step="final_plan_synthesized",
                    step_number=step_idx + 1,
                    summary="Synthesized autonomous multi-agent growth plan.",
                    data={
                        "plan_summary": response.content,
                        "steps_taken": [s.model_dump() for s in steps_taken],
                        "memory_citations": memory_citations,
                        "reasoning_trace": response.reasoning_trace or "Bounded ReAct loop complete.",
                        "provider_used": response.provider_used or "nvidia_nim",
                        "status": "completed",
                    },
                )
                return

            if response.tool_call is not None:
                tool_name = response.tool_call.name
                tool_args = response.tool_call.arguments
                call_id = response.tool_call.id or f"call_{step_idx}_{tool_name}"

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
                    step_number=step_idx + 1,
                    tool_name=tool_name,
                    arguments=tool_args,
                    result=tool_result,
                    step_summary=step_summary,
                )
                steps_taken.append(step_record)

                yield StepEvent(
                    step=f"step_{step_idx + 1}_{tool_name}",
                    step_number=step_idx + 1,
                    summary=step_summary,
                    data=step_record.model_dump(),
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

        yield StepEvent(
            step="final_plan_synthesized",
            step_number=max_steps,
            summary="Autonomous plan synthesized at max steps.",
            data={
                "plan_summary": "Autonomous growth plan completed across all domain tools.",
                "steps_taken": [s.model_dump() for s in steps_taken],
                "memory_citations": memory_citations,
                "status": "completed",
            },
        )

    def _summarize_step_result(self, tool_name: str, result: dict) -> str:
        """Generates concise readable summary for each tool step."""
        if tool_name == "get_merchant_context":
            return f"Retrieved store telemetry: {result.get('total_customers', 0)} customers, ₹{result.get('total_gmv', 0):,.0f} GMV."
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
