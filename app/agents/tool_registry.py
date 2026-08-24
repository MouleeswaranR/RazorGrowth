import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import CustomerModel
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.models.product import ProductModel
from app.services.context_engine import context_engine
from app.intelligence.opportunity_detector import detect_all_opportunities
from app.agents.customer_agent import CustomerAgent
from app.agents.offer_agent import OfferAgent
from app.services.permission_gate_service import permission_gate_service
from app.services.vector_memory_service import vector_memory_service

logger = logging.getLogger(__name__)

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_merchant_context",
            "description": "Fetch aggregated store telemetry including customer counts, orders, GMV, and payment success rates.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_opportunities",
            "description": "Run AI revenue leakage detectors and return ranked opportunities.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_audience",
            "description": "Select and rank target customer cohort for a specific opportunity type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "opportunity_type": {
                        "type": "string",
                        "description": "The opportunity type, e.g. customer_churn_prevention or payment_optimization",
                    },
                },
                "required": ["opportunity_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_offer",
            "description": "Determine optimal margin-safe discount offer for a target customer segment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "segment": {"type": "string", "description": "Target segment name, e.g. VIP Dormant"},
                    "average_spend": {"type": "number", "description": "Average historical spend in INR"},
                },
                "required": ["segment"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_similar_past_campaigns",
            "description": "Search vector memory for similar past growth campaigns and their measured lift outcomes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query describing the campaign or cohort"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_permission_gate",
            "description": "Evaluate dynamic financial guardrails for proposed offer code and audience size.",
            "parameters": {
                "type": "object",
                "properties": {
                    "discount_value": {"type": "number", "description": "Proposed discount percentage"},
                    "audience_count": {"type": "integer", "description": "Number of targeted customers"},
                    "target_segment": {"type": "string", "description": "Target segment name"},
                },
                "required": ["discount_value", "audience_count"],
            },
        },
    },
]


class ToolRegistry:
    """Dispatches tool calls to specialized agent capabilities and intelligence services."""

    def __init__(self) -> None:
        """Initializes domain agent dependencies for tool dispatch."""
        self._customer_agent = CustomerAgent()
        self._offer_agent = OfferAgent()

    async def _resolve_merchant_records(self, session: AsyncSession, merchant_id: str):
        """Fetches customer, order, payment, and product records for the target merchant."""
        customers = (await session.execute(select(CustomerModel).where(CustomerModel.merchant_id == merchant_id))).scalars().all()
        if not customers:
            first_cust = (await session.execute(select(CustomerModel))).scalars().first()
            if first_cust:
                merchant_id = first_cust.merchant_id
                customers = (await session.execute(select(CustomerModel).where(CustomerModel.merchant_id == merchant_id))).scalars().all()

        orders = (await session.execute(select(OrderModel).where(OrderModel.merchant_id == merchant_id))).scalars().all()
        payments = (await session.execute(select(PaymentModel).join(OrderModel, PaymentModel.order_id == OrderModel.id).where(OrderModel.merchant_id == merchant_id))).scalars().all()
        products = (await session.execute(select(ProductModel).where(ProductModel.merchant_id == merchant_id))).scalars().all()

        return merchant_id, list(customers), list(orders), list(payments), list(products)

    async def execute_tool(
        self,
        session: AsyncSession,
        merchant_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Routes tool execution request to appropriate underlying service."""
        if tool_name == "get_merchant_context":
            resolved_id, customers, orders, payments, products = await self._resolve_merchant_records(session, merchant_id)
            return context_engine.build_merchant_growth_context(resolved_id, customers, orders, payments, products)

        if tool_name == "detect_opportunities":
            resolved_id, customers, orders, payments, products = await self._resolve_merchant_records(session, merchant_id)
            opps = detect_all_opportunities(resolved_id, customers, orders, payments, {p.id: p.category for p in products})
            return {"opportunities_found": len(opps), "opportunities": [{"id": o.id, "title": o.title, "type": o.opportunity_type, "estimated_gmv": o.estimated_gmv_impact, "confidence": o.confidence_score} for o in opps]}

        if tool_name == "select_audience":
            opp_type = arguments.get("opportunity_type", "customer_churn_prevention")
            _, customers, _, _, _ = await self._resolve_merchant_records(session, merchant_id)
            target_segment = "VIP Dormant" if opp_type == "customer_churn_prevention" else "Cross-Sell Cohort"
            selected = self._customer_agent.filter_dormant_high_value_customers(customers) if opp_type == "customer_churn_prevention" else self._customer_agent.filter_active_customers(customers)
            aud = self._customer_agent.build_structured_audience("agentic_opp", target_segment, selected)
            return {"target_segment": target_segment, "audience_count": aud.total_audience_count, "avg_spend": sum(c.total_spend for c in aud.target_customers) / max(1, len(aud.target_customers)), "reasoning": aud.reasoning}

        if tool_name == "recommend_offer":
            segment = arguments.get("segment", "VIP Dormant")
            avg_spend = float(arguments.get("average_spend", 3500.0))
            offer = self._offer_agent.determine_optimal_offer(segment, avg_spend)
            return offer.model_dump()

        if tool_name == "recall_similar_past_campaigns":
            query = arguments.get("query", "VIP Dormant re-engagement campaign")
            memories = vector_memory_service.find_similar_memories(merchant_id, query, top_k=3)
            return {"retrieved_memories": memories}

        if tool_name == "check_permission_gate":
            customers = (await session.execute(select(CustomerModel).where(CustomerModel.merchant_id == merchant_id))).scalars().all()
            total_gmv = sum(c.total_spend_amount for c in customers)
            thresholds = permission_gate_service.calculate_dynamic_thresholds(len(customers), total_gmv, float(arguments.get("average_spend", 3500.0)), arguments.get("target_segment", "VIP Dormant"))
            max_disc = thresholds.get("max_discount_percentage", 20.0)
            max_aud = thresholds.get("max_auto_audience", 50.0)
            disc_val = float(arguments.get("discount_value", 15.0))
            aud_cnt = int(arguments.get("audience_count", 50))
            is_safe = disc_val <= max_disc and aud_cnt <= max_aud
            return {"is_safe": is_safe, "thresholds": thresholds, "policy_status": "auto_approved" if is_safe else "requires_merchant_approval"}

        return {"error": f"Tool '{tool_name}' not recognized"}


tool_registry = ToolRegistry()
