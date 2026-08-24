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
        """Fetches customer, order, payment, and product records for the target merchant.

        Scoped strictly to the requested merchant: an unknown or empty merchant yields
        empty record sets rather than silently substituting another merchant's data.
        """
        customers = (await session.execute(select(CustomerModel).where(CustomerModel.merchant_id == merchant_id))).scalars().all()
        if not customers:
            logger.warning(f"No customers found for merchant '{merchant_id}'; returning empty record set.")
            return merchant_id, [], [], [], []

        orders = (await session.execute(select(OrderModel).where(OrderModel.merchant_id == merchant_id))).scalars().all()
        payments = (await session.execute(select(PaymentModel).join(OrderModel, PaymentModel.order_id == OrderModel.id).where(OrderModel.merchant_id == merchant_id))).scalars().all()
        products = (await session.execute(select(ProductModel).where(ProductModel.merchant_id == merchant_id))).scalars().all()

        return merchant_id, list(customers), list(orders), list(payments), list(products)

    def _select_cohort_for_opportunity(
        self,
        opportunity_type: str,
        customers: list[CustomerModel],
    ) -> tuple[str, list[CustomerModel]]:
        """Maps an opportunity type to its target segment and filtered cohort.

        Mirrors the branching used by the campaign launch route so an agentic scan and a
        deterministic launch resolve the same audience for the same opportunity type.
        """
        if opportunity_type in ("customer_churn_prevention", "churn_prevention"):
            return "VIP Dormant", self._customer_agent.filter_dormant_high_value_customers(customers)

        if opportunity_type in ("payment_optimization", "payment_recovery"):
            slice_size = max(1, int(len(customers) * 0.20))
            return "payment_optimization", list(customers)[:slice_size]

        if opportunity_type in ("cross_sell_affinity", "cross_sell", "product_recommendation"):
            return "Cross-Sell Cohort", self._customer_agent.filter_active_customers(customers)

        if opportunity_type in ("aov_basket_builder", "basket_builder"):
            return "New", [c for c in customers if c.total_orders_count >= 2]

        return "Cross-Sell Cohort", self._customer_agent.filter_active_customers(customers)

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
            # Persist so the ids handed back are launchable: without this an agentic scan
            # surfaces opportunity ids that do not exist, and /campaigns/launch 404s.
            if opps:
                ranked = sorted(opps, key=lambda o: o.estimated_gmv_impact * o.confidence_score, reverse=True)
                session.add_all(ranked)
                await session.flush()
                opps = ranked
            return {
                "opportunities_found": len(opps),
                "opportunities": [
                    {
                        "id": o.id,
                        "title": o.title,
                        "type": o.opportunity_type,
                        "audience_count": o.target_audience_count,
                        "estimated_gmv": o.estimated_gmv_impact,
                        "confidence": o.confidence_score,
                    }
                    for o in opps
                ],
            }

        if tool_name == "select_audience":
            opp_type = arguments.get("opportunity_type", "customer_churn_prevention")
            _, customers, _, _, _ = await self._resolve_merchant_records(session, merchant_id)
            target_segment, selected = self._select_cohort_for_opportunity(opp_type, customers)
            aud = self._customer_agent.build_structured_audience("agentic_opp", target_segment, selected)
            return {
                "target_segment": target_segment,
                "opportunity_type": opp_type,
                "audience_count": aud.total_audience_count,
                "avg_spend": sum(c.total_spend for c in aud.target_customers) / max(1, len(aud.target_customers)),
                "reasoning": aud.reasoning,
            }

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
            # Derive average spend from live records rather than a magic default: this value
            # is not part of the tool schema, so the model cannot supply it, and a hardcoded
            # fallback would compute a safety threshold from fabricated input.
            derived_avg_spend = total_gmv / max(1, len(customers))
            avg_spend = float(arguments.get("average_spend") or derived_avg_spend)
            thresholds = permission_gate_service.calculate_dynamic_thresholds(len(customers), total_gmv, avg_spend, arguments.get("target_segment", "VIP Dormant"))
            max_disc = thresholds.get("max_discount_percentage", 20.0)
            max_aud = thresholds.get("max_auto_audience", 50.0)
            disc_val = float(arguments.get("discount_value", 15.0))
            aud_cnt = int(arguments.get("audience_count", 50))
            is_safe = disc_val <= max_disc and aud_cnt <= max_aud
            return {
                "is_safe": is_safe,
                "thresholds": thresholds,
                "evaluated_against": {
                    "total_customers": len(customers),
                    "total_gmv_inr": round(total_gmv, 2),
                    "average_spend_inr": round(avg_spend, 2),
                    "target_segment": arguments.get("target_segment", "VIP Dormant"),
                },
                "proposed": {"discount_value": disc_val, "audience_count": aud_cnt},
                "breach_reason": (
                    None if is_safe
                    else f"discount {disc_val}% > {max_disc}% cap" if disc_val > max_disc
                    else f"audience {aud_cnt} > {int(max_aud)} auto-approval cap"
                ),
                "policy_status": "auto_approved" if is_safe else "requires_merchant_approval",
            }

        return {"error": f"Tool '{tool_name}' not recognized"}


tool_registry = ToolRegistry()
