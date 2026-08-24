import pytest
import math
from unittest.mock import patch, MagicMock
from app.services.embedding_service import embedding_service
from app.services.vector_memory_service import vector_memory_service
from app.services.trace_tool_service import trace_tool_service
from app.agents.agentic_orchestrator import agentic_orchestrator
from app.agents.tool_registry import tool_registry
from app.schemas.agent_outputs import LLMToolResponse, ToolCall


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def test_embedding_service_dimension_and_similarity():
    """Validates dense embedding vector length (384) and semantic cosine distance properties."""
    text_1 = "VIP dormant customer recovery campaign with 15% discount"
    text_2 = "Reactivating inactive high value customers using promotional coupon code"
    text_unrelated = "PostgreSQL database table vacuum and index optimization"

    vec_1 = embedding_service.embed_text(text_1)
    vec_2 = embedding_service.embed_text(text_2)
    vec_unrelated = embedding_service.embed_text(text_unrelated)

    assert len(vec_1) == 384
    assert len(vec_2) == 384
    assert len(vec_unrelated) == 384

    sim_related = _cosine_similarity(vec_1, vec_2)
    sim_unrelated = _cosine_similarity(vec_1, vec_unrelated)

    assert sim_related > sim_unrelated
    assert sim_related > 0.40


def test_vector_memory_storage_and_semantic_retrieval():
    """Validates storing outcome memory records in ChromaDB and semantic similarity search."""
    merchant_id = "merch_test_vector_123"

    vector_memory_service.store_memory(
        memory_id="mem_vip_test_1",
        merchant_id=merchant_id,
        memory_type="campaign_outcome",
        summary_text="VIP Dormant customer re-engagement campaign with coupon discount for inactive high value shoppers.",
        metadata={"campaign_id": "cmp_vip_1", "incremental_gmv": 45000.0},
    )

    vector_memory_service.store_memory(
        memory_id="mem_payment_test_2",
        merchant_id=merchant_id,
        memory_type="payment_optimization",
        summary_text="UPI checkout gateway failure optimization and payment drop-off recovery.",
        metadata={"campaign_id": "cmp_upi_2", "incremental_gmv": 12000.0},
    )

    # Query for dormant high-value customers
    results = vector_memory_service.find_similar_memories(
        merchant_id=merchant_id,
        query_text="VIP Dormant customer recovery discount",
        top_k=1,
    )

    assert len(results) >= 1
    assert "VIP Dormant" in results[0]["summary"]


def test_trace_tool_service_hybrid_routing():
    """Validates exact keyword routing for structured facts and vector fallback for general queries."""
    session_id = "sess_test_routing"

    # Exact keyword query should route to offer details
    res_offer = trace_tool_service.route_and_fetch_relevant_context("What is the offer discount code?", session_id)
    assert res_offer["tool"] == "get_campaign_offer_details"

    # Exact keyword query should route to experiment lift
    res_exp = trace_tool_service.route_and_fetch_relevant_context("Show me the conversion lift and A/B result", session_id)
    assert res_exp["tool"] == "get_experiment_lift_summary"

    # Unmatched query routes to hybrid vector memory summary fallback
    res_hybrid = trace_tool_service.route_and_fetch_relevant_context("Have we experienced similar merchant drop-off patterns before?", session_id)
    assert res_hybrid["tool"] == "hybrid_vector_memory_summary"
    assert "historical_similar_campaigns" in res_hybrid


def test_agentic_loop_safety_boundary():
    """Asserts that AgenticOrchestrator does not import or execute state-changing payment / live experiment services."""
    import app.agents.agentic_orchestrator as orch_module
    import inspect

    source = inspect.getsource(orch_module)

    # Verify no direct Razorpay client creation or live checkout session execution in orchestrator
    assert "razorpay_client.create_order" not in source
    assert "live_experiment_service.create_cohort_test_orders" not in source
    assert "LiveExperimentService" not in source


@pytest.mark.asyncio
async def test_agentic_orchestrator_bounded_execution():
    """Validates bounded ReAct tool loop executes up to MAX_STEPS without infinite loops."""
    from unittest.mock import AsyncMock
    from app.models.customer import CustomerModel
    from app.models.order import OrderModel
    from app.models.payment import PaymentModel
    from app.models.product import ProductModel

    mock_cust = CustomerModel(
        id="c1",
        merchant_id="merch_agentic_mock",
        name="Test Cust",
        email="test@example.com",
        customer_segment="VIP Dormant",
        total_orders_count=4,
        total_spend_amount=8000.0,
        churn_risk_score=0.85,
        predicted_lifetime_value=24000.0,
        favorite_category="Apparel",
    )
    mock_order = OrderModel(
        id="o1",
        merchant_id="merch_agentic_mock",
        customer_id="c1",
        amount=8000.0,
        status="completed",
    )
    mock_payment = PaymentModel(
        id="p1",
        order_id="o1",
        payment_method="upi",
        amount=8000.0,
        status="captured",
    )
    mock_product = ProductModel(
        id="pr1",
        merchant_id="merch_agentic_mock",
        title="Sample Product",
        category="Apparel",
        price=4000.0,
    )

    mock_session = AsyncMock()

    async def mock_exec(stmt):
        res = MagicMock()
        text_stmt = str(stmt).lower()
        if "customers" in text_stmt:
            res.scalars.return_value.all.return_value = [mock_cust]
        elif "orders" in text_stmt and "payments" not in text_stmt:
            res.scalars.return_value.all.return_value = [mock_order]
        elif "payments" in text_stmt:
            res.scalars.return_value.all.return_value = [mock_payment]
        elif "products" in text_stmt:
            res.scalars.return_value.all.return_value = [mock_product]
        else:
            res.scalars.return_value.all.return_value = []
        return res

    mock_session.execute.side_effect = mock_exec

    result = await agentic_orchestrator.run_agentic_growth_scan(
        session=mock_session,
        merchant_id="merch_agentic_mock",
    )

    assert result.merchant_id == "merch_agentic_mock"
    assert len(result.steps_taken) <= 6
    assert result.status in ("completed", "max_steps_reached")
    assert len(result.plan_summary) > 10

