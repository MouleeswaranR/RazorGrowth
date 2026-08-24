from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import CustomerModel
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.models.product import ProductModel
from app.intelligence.opportunity_detector import detect_all_opportunities
from app.agents.customer_agent import CustomerAgent
from app.agents.offer_agent import OfferAgent
from app.agents.campaign_agent import CampaignAgent
from app.services.context_engine import context_engine
from app.services.permission_gate_service import permission_gate_service
from app.services.llm_service import llm_service
from app.schemas.agent_outputs import GrowthPlanOutput, LLMReasoningInput






class GrowthManagerAgent:
    """Master orchestrator integrating ContextEngine, specialized agents, and Permission Gates."""

    def __init__(self) -> None:
        """Initializes agent dependencies."""
        self._customer_agent = CustomerAgent()
        self._offer_agent = OfferAgent()
        self._campaign_agent = CampaignAgent()

    async def execute_full_growth_scan(
        self,
        session: AsyncSession,
        merchant_id: str,
    ) -> dict:
        """Executes full scan using ContextEngine and PermissionGates, returning structured GrowthPlan."""
        customers = (await session.execute(
            select(CustomerModel).where(CustomerModel.merchant_id == merchant_id)
        )).scalars().all()

        orders = (await session.execute(
            select(OrderModel).where(OrderModel.merchant_id == merchant_id)
        )).scalars().all()

        payments = (await session.execute(
            select(PaymentModel).join(OrderModel, PaymentModel.order_id == OrderModel.id).where(OrderModel.merchant_id == merchant_id)
        )).scalars().all()

        products = (await session.execute(
            select(ProductModel).where(ProductModel.merchant_id == merchant_id)
        )).scalars().all()

        customer_list = list(customers)
        order_list = list(orders)
        payment_list = list(payments)
        product_list = list(products)
        product_category_map = {p.id: p.category for p in product_list}

        # 1. Build high-signal context using ContextEngine
        context = context_engine.build_merchant_growth_context(
            merchant_id, customer_list, order_list, payment_list, product_list,
        )

        # 2. Detect all opportunity types
        opportunities = detect_all_opportunities(
            merchant_id, customer_list, order_list, payment_list, product_category_map,
        )

        if not opportunities:
            return {"opportunities_found": 0, "opportunities": [], "action_plan": None}

        ranked = sorted(opportunities, key=lambda o: o.estimated_gmv_impact * o.confidence_score, reverse=True)
        session.add_all(ranked)
        await session.flush()

        top = ranked[0]

        # 2b. Recall similar past campaigns from ChromaDB vector memory
        from app.services.vector_memory_service import vector_memory_service
        recall_query = f"{top.title} {top.opportunity_type} discount recovery"
        memory_citations = vector_memory_service.find_similar_memories(
            merchant_id, recall_query, top_k=3
        )

        # 3. CustomerAgent builds structured audience
        if top.opportunity_type == "customer_churn_prevention":
            audience_models = self._customer_agent.filter_dormant_high_value_customers(customer_list)
            target_segment = "VIP Dormant"
        else:
            audience_models = self._customer_agent.filter_active_customers(customer_list)
            target_segment = "Cross-Sell Cohort"

        structured_audience = self._customer_agent.build_structured_audience(
            opportunity_id=top.id,
            target_segment=target_segment,
            selected_customers=audience_models,
        )

        # 4. OfferAgent builds structured offer
        avg_spend = sum(c.total_spend for c in structured_audience.target_customers) / max(1, len(structured_audience.target_customers))
        structured_offer = self._offer_agent.determine_optimal_offer(target_segment, avg_spend)

        # 5. CampaignAgent builds structured copy via LLMService
        structured_copy = await self._campaign_agent.compose_personalized_copy(
            customer_name="Valued Customer",
            offer_description=structured_offer.description,
            urgency=structured_offer.urgency_text,
            favorite_category="Apparel",
        )

        # 6. PermissionGateService evaluates safety policies against real store telemetry
        gate_decision = permission_gate_service.evaluate_campaign_safety(
            offer=structured_offer,
            audience=structured_audience,
            total_customers=len(customer_list),
            total_gmv=sum(c.total_spend_amount for c in customer_list),
        )

        # 7. LLMService generates executive reasoning using structured input
        llm_input = LLMReasoningInput(
            merchant_id=merchant_id,
            top_opportunity_title=top.title,
            total_opportunity_gmv=top.estimated_gmv_impact,
            total_customers=context.get("total_customers", 0),
            dormant_vip_count=context.get("dormant_vip_count", 0),
            payment_success_rate=context.get("payment_overall_success_rate", 0.0),
        )
        llm_output = await llm_service.generate_growth_reasoning(llm_input)

        plan = GrowthPlanOutput(
            merchant_id=merchant_id,
            opportunity_id=top.id,
            opportunity_title=top.title,
            estimated_gmv_impact=top.estimated_gmv_impact,
            confidence_score=top.confidence_score,
            audience=structured_audience,
            offer=structured_offer,
            campaign_copy=structured_copy,
            permission_gate=gate_decision,
            ai_reasoning=llm_output.executive_summary,
        )

        # Store growth scan summary in VectorMemoryService
        from app.services.vector_memory_service import vector_memory_service
        scan_summary = (
            f"Growth scan detected {len(ranked)} opportunities for {merchant_id}. "
            f"Top opportunity: '{top.title}' with ₹{top.estimated_gmv_impact:,.0f} estimated GMV impact. "
            f"AI Reasoning: {llm_output.executive_summary}"
        )
        vector_memory_service.store_memory(
            memory_id=f"mem_scan_{merchant_id}_{top.id[:10]}",
            merchant_id=merchant_id,
            memory_type="growth_scan",
            summary_text=scan_summary,
            metadata={
                "opportunity_id": top.id,
                "opportunity_type": top.opportunity_type,
                "estimated_gmv": float(top.estimated_gmv_impact),
                "confidence": float(top.confidence_score),
            },
        )

        return {
            "opportunities_found": len(ranked),
            "opportunities": [
                {
                    "id": o.id,
                    "title": o.title,
                    "type": o.opportunity_type,
                    "audience_count": o.target_audience_count,
                    "estimated_gmv": o.estimated_gmv_impact,
                    "confidence": o.confidence_score,
                }
                for o in ranked
            ],
            "action_plan": plan.model_dump(),
            "memory_citations": memory_citations,
        }

    async def stream_full_growth_scan(
        self,
        session: AsyncSession,
        merchant_id: str,
    ):
        """Streams step-by-step progress events as each agent completes its task in real time."""
        from app.schemas.agent_outputs import StepEvent

        customers = (await session.execute(
            select(CustomerModel).where(CustomerModel.merchant_id == merchant_id)
        )).scalars().all()

        orders = (await session.execute(
            select(OrderModel).where(OrderModel.merchant_id == merchant_id)
        )).scalars().all()

        payments = (await session.execute(
            select(PaymentModel).join(OrderModel, PaymentModel.order_id == OrderModel.id).where(OrderModel.merchant_id == merchant_id)
        )).scalars().all()

        products = (await session.execute(
            select(ProductModel).where(ProductModel.merchant_id == merchant_id)
        )).scalars().all()

        customer_list = list(customers)
        order_list = list(orders)
        payment_list = list(payments)
        product_list = list(products)
        product_category_map = {p.id: p.category for p in product_list}

        # Step 1: Merchant telemetry context built
        context = context_engine.build_merchant_growth_context(
            merchant_id, customer_list, order_list, payment_list, product_list,
        )
        yield StepEvent(
            step="1_telemetry_context_built",
            step_number=1,
            summary=f"Synthesized telemetry across {len(customer_list)} customers and {len(order_list)} orders.",
            data=context,
        )

        # Step 2: Opportunity detection & ranking
        opportunities = detect_all_opportunities(
            merchant_id, customer_list, order_list, payment_list, product_category_map,
        )
        if not opportunities:
            yield StepEvent(step="2_opportunities_detected", step_number=2, summary="No active revenue leaks detected.", data={"opportunities_found": 0})
            return

        ranked = sorted(opportunities, key=lambda o: o.estimated_gmv_impact * o.confidence_score, reverse=True)
        session.add_all(ranked)
        await session.flush()
        top = ranked[0]

        opp_list = [
            {
                "id": o.id,
                "title": o.title,
                "type": o.opportunity_type,
                "audience_count": o.target_audience_count,
                "estimated_gmv": o.estimated_gmv_impact,
                "confidence": o.confidence_score,
            }
            for o in ranked
        ]
        yield StepEvent(
            step="2_opportunities_detected",
            step_number=2,
            summary=f"Diagnosed {len(ranked)} opportunities. Top: '{top.title}' (₹{top.estimated_gmv_impact:,.0f} impact).",
            data={"opportunities": opp_list, "top_opportunity": top.title},
        )

        # Step 2b: Recall similar past campaigns from ChromaDB vector memory
        from app.services.vector_memory_service import vector_memory_service
        recall_query = f"{top.title} {top.opportunity_type} discount recovery"
        recalled_memories = vector_memory_service.find_similar_memories(
            merchant_id, recall_query, top_k=3
        )
        yield StepEvent(
            step="2b_vector_memory_recall",
            step_number=2,
            summary=f"Retrieved {len(recalled_memories)} similar past campaign benchmarks from ChromaDB.",
            data={"query": recall_query, "retrieved_memories": recalled_memories},
        )

        # Step 3: CustomerAgent audience selection
        if top.opportunity_type == "customer_churn_prevention":
            audience_models = self._customer_agent.filter_dormant_high_value_customers(customer_list)
            target_segment = "VIP Dormant"
        else:
            audience_models = self._customer_agent.filter_active_customers(customer_list)
            target_segment = "Cross-Sell Cohort"

        structured_audience = self._customer_agent.build_structured_audience(
            opportunity_id=top.id,
            target_segment=target_segment,
            selected_customers=audience_models,
        )
        yield StepEvent(
            step="3_audience_selected",
            step_number=3,
            summary=f"Segmented {structured_audience.total_audience_count} high-CLV customers ({target_segment}).",
            data=structured_audience.model_dump(),
        )

        # Step 4: OfferAgent incentive calibration
        avg_spend = sum(c.total_spend for c in structured_audience.target_customers) / max(1, len(structured_audience.target_customers))
        structured_offer = self._offer_agent.determine_optimal_offer(target_segment, avg_spend)
        yield StepEvent(
            step="4_offer_calibrated",
            step_number=4,
            summary=f"Formulated incentive '{structured_offer.offer_code}': {structured_offer.description}",
            data=structured_offer.model_dump(),
        )

        # Step 5: CampaignAgent copy generation
        structured_copy = await self._campaign_agent.compose_personalized_copy(
            customer_name="Valued Customer",
            offer_description=structured_offer.description,
            urgency=structured_offer.urgency_text,
            favorite_category="Apparel",
        )
        yield StepEvent(
            step="5_copy_composed",
            step_number=5,
            summary="Generated individualized messaging for Email/WhatsApp channels.",
            data=structured_copy.model_dump(),
        )

        # Step 6: PermissionGate policy evaluation against real store telemetry
        gate_decision = permission_gate_service.evaluate_campaign_safety(
            offer=structured_offer,
            audience=structured_audience,
            total_customers=len(customer_list),
            total_gmv=sum(c.total_spend_amount for c in customer_list),
        )
        yield StepEvent(
            step="6_permission_gate_evaluated",
            step_number=6,
            summary=f"Permission Gate Status: {gate_decision.status.value}. Notes: {gate_decision.policy_notes}",
            data=gate_decision.model_dump(),
        )

        # Step 7: LLM strategic executive reasoning
        llm_input = LLMReasoningInput(
            merchant_id=merchant_id,
            top_opportunity_title=top.title,
            total_opportunity_gmv=top.estimated_gmv_impact,
            total_customers=context.get("total_customers", 0),
            dormant_vip_count=context.get("dormant_vip_count", 0),
            payment_success_rate=context.get("payment_overall_success_rate", 0.0),
        )
        llm_output = await llm_service.generate_growth_reasoning(llm_input)

        plan = GrowthPlanOutput(
            merchant_id=merchant_id,
            opportunity_id=top.id,
            opportunity_title=top.title,
            estimated_gmv_impact=top.estimated_gmv_impact,
            confidence_score=top.confidence_score,
            audience=structured_audience,
            offer=structured_offer,
            campaign_copy=structured_copy,
            permission_gate=gate_decision,
            ai_reasoning=llm_output.executive_summary,
        )

        # Store in Vector Memory
        from app.services.vector_memory_service import vector_memory_service
        scan_summary = (
            f"Growth scan detected {len(ranked)} opportunities for {merchant_id}. "
            f"Top opportunity: '{top.title}' with ₹{top.estimated_gmv_impact:,.0f} estimated GMV impact. "
            f"AI Reasoning: {llm_output.executive_summary}"
        )
        vector_memory_service.store_memory(
            memory_id=f"mem_scan_{merchant_id}_{top.id[:10]}",
            merchant_id=merchant_id,
            memory_type="growth_scan",
            summary_text=scan_summary,
            metadata={
                "opportunity_id": top.id,
                "opportunity_type": top.opportunity_type,
                "estimated_gmv": float(top.estimated_gmv_impact),
                "confidence": float(top.confidence_score),
            },
        )

        yield StepEvent(
            step="7_growth_plan_finalized",
            step_number=7,
            summary=f"Finalized Growth Plan with ₹{top.estimated_gmv_impact:,.0f} projected GMV recovery.",
            data={
                "opportunities_found": len(ranked),
                "opportunities": opp_list,
                "action_plan": plan.model_dump(),
            },
        )

