from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_database_session
from app.models.customer import CustomerModel
from app.models.payment import PaymentModel
from app.models.order import OrderModel, PAID_ORDER_STATUSES
from app.agents.growth_manager_agent import GrowthManagerAgent
from app.services.llm_service import llm_service
from app.services.trace_logger_service import trace_logger_service
from app.schemas.agent_outputs import LLMChatInput, LLMReasoningInput

router = APIRouter(prefix="/growth", tags=["Growth Opportunities & AI Agent"])


class ChatRequest(BaseModel):
    """Schema for merchant interactive chat queries."""
    merchant_id: str
    session_id: str | None = None
    query: str


@router.post("/scan/{merchant_id}")
async def scan_growth_opportunities(
    merchant_id: str,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Runs full multi-agent growth scan and logs trace output for the active session."""
    agent = GrowthManagerAgent()
    result = await agent.execute_full_growth_scan(session, merchant_id)
    await session.commit()

    step_data = {
        "opportunities_found": result["opportunities_found"],
        "opportunities": result["opportunities"],
        "action_plan": result["action_plan"],
    }
    trace_logger_service.log_trace_step(
        run_id=merchant_id,
        session_id=session_id,
        step_name="2_opportunity_scan_and_ai_reasoning",
        step_data=step_data,
    )

    return {
        "status": "success",
        "session_id": session_id or merchant_id,
        "opportunities_found": result["opportunities_found"],
        "opportunities": result["opportunities"],
        "action_plan": result["action_plan"],
    }


@router.get("/scan-live/{merchant_id}")
async def scan_growth_opportunities_live(
    merchant_id: str,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
):
    """Streams live step-by-step multi-agent growth scan events via SSE with natural step pacing."""
    import json
    import asyncio
    agent = GrowthManagerAgent()

    async def event_generator():
        async for event in agent.stream_full_growth_scan(session, merchant_id):
            trace_logger_service.log_trace_step(
                run_id=merchant_id,
                session_id=session_id,
                step_name=event.step,
                step_data=event.data if isinstance(event.data, dict) else {"content": event.data},
            )
            if event.step == "7_growth_plan_finalized":
                trace_logger_service.log_trace_step(
                    run_id=merchant_id,
                    session_id=session_id,
                    step_name="2_opportunity_scan_and_ai_reasoning",
                    step_data=event.data,
                )
            yield f"data: {json.dumps(event.model_dump())}\n\n"
            # Visual pacing delay so each agent step is distinctly visible and inspectable
            await asyncio.sleep(0.55)

        await session.commit()
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/agentic-scan/{merchant_id}")
async def agentic_growth_scan(
    merchant_id: str,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Executes LLM-driven bounded agentic loop with tool calling and vector memory recall."""
    from app.agents.agentic_orchestrator import agentic_orchestrator

    result = await agentic_orchestrator.run_agentic_growth_scan(session, merchant_id)
    await session.commit()

    step_data = {
        "plan_summary": result.plan_summary,
        "steps_taken": [s.model_dump() for s in result.steps_taken],
        "memory_citations": result.memory_citations,
        "status": result.status,
    }
    trace_logger_service.log_trace_step(
        run_id=merchant_id,
        session_id=session_id,
        step_name="2_agentic_decision_loop",
        step_data=step_data,
    )

    return {
        "status": "success",
        "mode": "agentic_react_loop",
        "merchant_id": merchant_id,
        "session_id": session_id or merchant_id,
        "plan_summary": result.plan_summary,
        "steps_taken": [s.model_dump() for s in result.steps_taken],
        "memory_citations": result.memory_citations,
        "reasoning_trace": result.reasoning_trace,
        "provider_used": result.provider_used,
        "status_detail": result.status,
    }


@router.get("/agentic-scan-live/{merchant_id}")
async def agentic_growth_scan_live(
    merchant_id: str,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
):
    """Streams live step-by-step bounded agentic tool execution events via SSE."""
    import json
    from app.agents.agentic_orchestrator import agentic_orchestrator

    async def event_generator():
        async for event in agentic_orchestrator.stream_agentic_growth_scan(session, merchant_id):
            trace_logger_service.log_trace_step(
                run_id=merchant_id,
                session_id=session_id,
                step_name=event.step,
                step_data=event.data if isinstance(event.data, dict) else {"content": event.data},
            )
            if event.step == "final_plan_synthesized":
                trace_logger_service.log_trace_step(
                    run_id=merchant_id,
                    session_id=session_id,
                    step_name="2_agentic_decision_loop",
                    step_data=event.data,
                )
            yield f"data: {json.dumps(event.model_dump())}\n\n"
        await session.commit()
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/latest-trace")
async def get_latest_execution_trace(session_id: str | None = None) -> dict:
    """Retrieves the full multi-step execution trace for a session from the local output/ folder."""
    if session_id:
        trace = trace_logger_service.get_session_trace(session_id)
        if not trace:
            trace = trace_logger_service.get_session_trace(f"session_{session_id}")
    else:
        trace = trace_logger_service.get_latest_trace()
    if not trace:
        return {"status": "empty", "message": "No trace recorded yet for this session.", "data": None, "steps": {}}
    return {"status": "success", "data": trace}


@router.get("/stream-reasoning/{merchant_id}")
async def stream_growth_reasoning(
    merchant_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> StreamingResponse:
    """Streams live token-by-token strategic growth reasoning from RazorGrowth AI Engine."""
    customers = (await session.execute(
        select(CustomerModel).where(CustomerModel.merchant_id == merchant_id)
    )).scalars().all()

    orders = (await session.execute(
        select(OrderModel).where(OrderModel.merchant_id == merchant_id)
    )).scalars().all()

    payments = (await session.execute(
        select(PaymentModel).join(OrderModel, PaymentModel.order_id == OrderModel.id).where(OrderModel.merchant_id == merchant_id)
    )).scalars().all()

    dormant_count = sum(1 for c in customers if c.customer_segment in ("VIP Dormant", "Loyal At Risk"))
    total_gmv = sum(o.amount for o in orders if o.status in PAID_ORDER_STATUSES)
    success_rate = sum(1 for p in payments if p.status == "captured") / max(1, len(payments))

    input_data = LLMReasoningInput(
        merchant_id=merchant_id,
        top_opportunity_title="Dormant VIP Recovery & Payment Optimization",
        total_opportunity_gmv=round(total_gmv * 0.18, 2),
        total_customers=len(customers),
        dormant_vip_count=dormant_count,
        payment_success_rate=round(success_rate, 4),
    )

    async def event_generator():
        async for chunk in llm_service.stream_growth_reasoning(input_data):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _build_chat_input(session: AsyncSession, request: "ChatRequest") -> LLMChatInput:
    """Assembles grounded chat input using SQL aggregates.

    The prompt only needs three scalars, so aggregate in the database rather than
    materialising every customer and order row over the network.
    """
    dormant_count, total_customers = (await session.execute(
        select(
            func.count(CustomerModel.id).filter(
                CustomerModel.customer_segment.in_(("VIP Dormant", "Loyal At Risk"))
            ),
            func.count(CustomerModel.id),
        ).where(CustomerModel.merchant_id == request.merchant_id)
    )).one()

    total_gmv = (await session.execute(
        select(func.coalesce(func.sum(OrderModel.amount), 0.0)).where(
            OrderModel.merchant_id == request.merchant_id,
            OrderModel.status.in_(PAID_ORDER_STATUSES),
        )
    )).scalar_one()

    return LLMChatInput(
        merchant_id=request.merchant_id,
        session_id=request.session_id,
        query=request.query,
        total_customers=int(total_customers or 0),
        total_revenue=round(float(total_gmv or 0.0), 2),
        dormant_vip_count=int(dormant_count or 0),
    )


@router.post("/chat-stream")
async def chat_with_growth_strategist_stream(
    request: ChatRequest,
    session: AsyncSession = Depends(get_database_session),
):
    """Streams the strategist's answer token-by-token over SSE for immediate perceived response."""
    import json as _json

    chat_input = await _build_chat_input(session, request)

    async def event_generator():
        try:
            async for event in llm_service.stream_chat_with_merchant(chat_input):
                yield f"data: {_json.dumps(event)}\n\n"
        except Exception as err:
            yield f"data: {_json.dumps({'type': 'error', 'message': str(err)[:200]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat")
async def chat_with_growth_strategist(
    request: ChatRequest,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Answers merchant questions with targeted session-trace micro-tools and reasoning traces."""
    chat_input = await _build_chat_input(session, request)
    result = await llm_service.chat_with_merchant(chat_input)

    return {
        "status": "success",
        "reply": result.reply,
        "suggested_follow_up": result.suggested_follow_up_action,
        "reasoning_trace": result.reasoning_trace,
        "provider_used": result.provider_used,
        "tools_used": result.tools_used,
        "tool_data": result.tool_data,
    }


@router.get("/sessions")
async def list_recent_sessions() -> dict:
    """Returns all recorded execution traces for session switching and cross-referencing."""
    sessions = trace_logger_service.list_all_sessions()
    return {
        "status": "success",
        "total_sessions": len(sessions),
        "sessions": sessions,
    }


class CrossReferenceRequest(BaseModel):
    """Schema for cross-referencing between sessions."""
    current_session_id: str
    target_session_id: str | None = None
    query: str = "Compare conversion lift, audience targeting, and revenue recovery between sessions."


@router.post("/cross-reference")
async def cross_reference_sessions(
    request: CrossReferenceRequest,
) -> dict:
    """Performs comparative RAG analysis across sessions using Vector Memory and Trace Logs."""
    from app.services.vector_memory_service import vector_memory_service
    from app.services.trace_tool_service import trace_tool_service

    current_summary = trace_tool_service.get_experiment_lift_summary(request.current_session_id)
    current_audience = trace_tool_service.get_audience_breakdown(request.current_session_id)

    target_summary = {}
    target_audience = {}
    if request.target_session_id:
        target_summary = trace_tool_service.get_experiment_lift_summary(request.target_session_id)
        target_audience = trace_tool_service.get_audience_breakdown(request.target_session_id)

    # Cross-session comparison is intentionally allowed to surface memories beyond the
    # current session/merchant, so opt out of the strict per-merchant scoping here.
    similar_memories = vector_memory_service.find_similar_memories(
        merchant_id=request.current_session_id,
        query_text=request.query,
        top_k=4,
        strict_merchant=False,
    )

    comparison_narrative = ""
    if request.target_session_id:
        # Ask LLM to synthesize comparative analysis
        chat_prompt = (
            f"Compare the current session ({request.current_session_id}) with "
            f"benchmark session {request.target_session_id}.\n\n"
            f"## Current Session:\n{current_summary}\nAudience: {current_audience}\n\n"
            f"## Target Session:\n{target_summary}\nAudience: {target_audience}\n\n"
            f"## Vector Memory Context:\n{similar_memories}\n\n"
            f"Summarize key differences in conversion lift, incentive strategy, and net incremental GMV in 2-3 concise bullet points."
        )

        comparison_chat = LLMChatInput(
            merchant_id=request.current_session_id,
            session_id=request.current_session_id,
            query=chat_prompt,
            total_customers=current_audience.get("total_audience", 50),
            total_revenue=0.0,
            dormant_vip_count=0,
        )
        analysis = await llm_service.chat_with_merchant(comparison_chat)
        comparison_narrative = analysis.reply
    else:
        comparison_narrative = f"Retrieved {len(similar_memories)} episodic memory benchmarks from ChromaDB vector store."

    return {
        "status": "success",
        "current_session_id": request.current_session_id,
        "target_session_id": request.target_session_id,
        "comparison_narrative": comparison_narrative,
        "current_metrics": current_summary,
        "target_metrics": target_summary,
        "vector_memories": similar_memories,
    }
