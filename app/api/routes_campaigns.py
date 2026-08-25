import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_database_session
from app.models.customer import CustomerModel
from app.models.opportunity import OpportunityModel
from app.models.campaign import CampaignModel
from app.agents.customer_agent import CustomerAgent
from app.agents.offer_agent import OfferAgent
from app.agents.experiment_agent import ExperimentAgent
from app.services.permission_gate_service import permission_gate_service
from app.schemas.agent_outputs import ApprovalStatus, PermissionGateResult
from app.actions.campaign_dispatcher import campaign_dispatcher
from app.services.trace_logger_service import trace_logger_service

router = APIRouter(prefix="/campaigns", tags=["Autonomous Campaigns"])


@router.post("/launch/{opportunity_id}")
async def launch_campaign(
    opportunity_id: str,
    bypass_permission_gate: bool = False,
    max_audience_cap: int | None = None,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Launches opportunity-aligned campaign through dynamic Permission Gate safety checks."""
    opportunity = (await session.execute(
        select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
    )).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    customers = (await session.execute(
        select(CustomerModel).where(CustomerModel.merchant_id == opportunity.merchant_id)
    )).scalars().all()

    customer_agent = CustomerAgent()
    offer_agent = OfferAgent()
    experiment_agent = ExperimentAgent()

    # Align audience filtering and target strategy with the specific opportunity type
    if opportunity.opportunity_type in ("customer_churn_prevention", "churn_prevention"):
        selected_customers = customer_agent.filter_dormant_high_value_customers(list(customers))
        target_segment = "VIP Dormant"
    elif opportunity.opportunity_type in ("payment_optimization", "payment_recovery"):
        default_payment_slice = max(1, int(len(customers) * 0.20))
        target_count = min(len(customers), opportunity.target_audience_count or default_payment_slice)
        selected_customers = list(customers)[:target_count]
        target_segment = "payment_optimization"
    elif opportunity.opportunity_type in ("cross_sell_affinity", "cross_sell", "product_recommendation"):
        selected_customers = customer_agent.filter_active_customers(list(customers))
        target_segment = "Loyal"
    elif opportunity.opportunity_type in ("aov_basket_builder", "basket_builder"):
        selected_customers = [c for c in customers if c.total_orders_count >= 2]
        target_segment = "New"
    else:
        selected_customers = customer_agent.filter_active_customers(list(customers))
        target_segment = "Target Cohort"

    # Fallback to general customer sample if filter returned zero
    if not selected_customers:
        target_count = min(len(customers), opportunity.target_audience_count or 50)
        selected_customers = list(customers)[:target_count]
        if not target_segment or target_segment == "Target Cohort":
            target_segment = "VIP Dormant" if "Dormant" in opportunity.title else "Loyal"

    # Prioritize highest value customers
    selected_customers.sort(
        key=lambda c: (c.total_spend_amount, c.predicted_lifetime_value),
        reverse=True,
    )

    eligible_count = len(selected_customers)

    # Apply audience cap if requested by merchant to stay within safe guardrails
    if max_audience_cap and max_audience_cap > 0:
        selected_customers = selected_customers[:max_audience_cap]

    structured_audience = customer_agent.build_structured_audience(
        opportunity_id=opportunity.id,
        target_segment=target_segment,
        selected_customers=selected_customers,
    )

    avg_spend = sum(c.total_spend for c in structured_audience.target_customers) / max(1, len(structured_audience.target_customers))
    total_gmv = sum(c.total_spend_amount for c in customers)
    structured_offer = offer_agent.determine_optimal_offer(target_segment, avg_spend)

    # Dynamic threshold calculation
    thresholds = permission_gate_service.calculate_dynamic_thresholds(
        total_customers=len(customers),
        total_gmv=total_gmv,
        average_spend=avg_spend,
        target_segment=target_segment,
    )

    if bypass_permission_gate:
        gate_decision = PermissionGateResult(
            status=ApprovalStatus.AUTO_APPROVED,
            is_executable=True,
            policy_notes="Permission Gate manually approved & authorized by merchant override.",
            max_allowed_discount_percentage=structured_offer.discount_value,
            estimated_cost_inr=structured_audience.total_audience_count * 2.5,
            reasoning="Merchant explicitly authorized execution beyond standard safety boundaries.",
        )
    else:
        gate_decision = permission_gate_service.evaluate_campaign_safety(
            offer=structured_offer,
            audience=structured_audience,
            total_customers=len(customers),
            total_gmv=total_gmv,
        )

        if gate_decision.status == ApprovalStatus.REQUIRES_MERCHANT_APPROVAL:
            return {
                "status": "requires_approval",
                "opportunity_id": opportunity.id,
                "permission_gate": gate_decision.model_dump(),
                "eligible_audience": eligible_count,
                "total_audience": len(selected_customers),
                "safe_audience_cap": int(thresholds["max_auto_audience"]),
                "offer": structured_offer.model_dump(),
                "message": gate_decision.policy_notes,
            }

    manifest = [c.model_dump() for c in structured_audience.target_customers]
    treatment_group, control_group = experiment_agent.split_cohort(manifest, treatment_ratio=0.80)

    dispatched = await campaign_dispatcher.execute_email_campaign(
        target_customers=treatment_group,
        offer_code=structured_offer.offer_code,
        offer_description=structured_offer.description,
        discount_type=structured_offer.discount_type,
        discount_value=structured_offer.discount_value,
        min_order_value=structured_offer.min_order_value,
        campaign_type=opportunity.opportunity_type,
    )

    campaign = CampaignModel(
        id=f"cmp_{uuid.uuid4().hex[:12]}",
        opportunity_id=opportunity.id,
        name=f"Campaign: {opportunity.title}",
        channel="email",
        offer_details=structured_offer.description,
        message_copy=f"Code: {structured_offer.offer_code}",
        status="active",
        target_customer_count=len(manifest),
    )
    session.add(campaign)
    opportunity.status = "actioned"
    await session.commit()

    from app.services.live_experiment_service import live_experiment_service
    control_checkout_amount = avg_spend
    treatment_checkout_amount = avg_spend
    if structured_offer.discount_type == "percentage":
        treatment_checkout_amount *= 1 - (structured_offer.discount_value / 100)
    elif structured_offer.discount_type == "fixed":
        treatment_checkout_amount -= structured_offer.discount_value
    treatment_checkout_amount = max(1.0, round(treatment_checkout_amount, 2))

    checkout_sessions = await live_experiment_service.create_cohort_test_orders(
        session=session,
        campaign_id=campaign.id,
        merchant_id=opportunity.merchant_id,
        treatment_customers=treatment_group,
        control_customers=control_group,
        treatment_amount=treatment_checkout_amount,
        control_amount=control_checkout_amount,
        session_id=session_id,
    )

    # Log to session trace
    trace_logger_service.log_trace_step(
        run_id=opportunity.merchant_id,
        session_id=session_id,
        step_name="3_campaign_launch_and_dispatch",
        step_data={
            "campaign_id": campaign.id,
            "opportunity_id": opportunity.id,
            "opportunity_type": opportunity.opportunity_type,
            "permission_gate": gate_decision.model_dump(),
            "target_segment": target_segment,
            "audience_reasoning": structured_audience.reasoning,
            "offer_reasoning": structured_offer.reasoning,
            "eligible_audience": eligible_count,
            "total_audience": len(manifest),
            "treatment_group_size": len(treatment_group),
            "control_group_size": len(control_group),
            "emails_dispatched": dispatched,
            "offer": structured_offer.model_dump(),
            "razorpay_test_orders_created": len(checkout_sessions),
        },
    )

    mock_order_count = sum(1 for s in checkout_sessions if s.get("is_mock"))

    return {
        "status": "launched",
        "campaign_id": campaign.id,
        "permission_gate": gate_decision.model_dump(),
        "eligible_audience": eligible_count,
        "total_audience": len(manifest),
        "treatment_group_size": len(treatment_group),
        "control_group_size": len(control_group),
        "emails_dispatched": dispatched,
        "offer": structured_offer.model_dump(),
        "checkout_sessions": checkout_sessions[:3] + [
            checkout for checkout in checkout_sessions
            if checkout["variant"] == "control"
        ][:3],
        "total_test_orders": len(checkout_sessions),
        "live_razorpay_orders": len(checkout_sessions) - mock_order_count,
        "mock_razorpay_orders": mock_order_count,
    }
