import pytest
from app.models.customer import CustomerModel
from app.agents.customer_agent import CustomerAgent
from app.agents.offer_agent import OfferAgent
from app.agents.campaign_agent import CampaignAgent
from app.agents.experiment_agent import ExperimentAgent
from app.schemas.agent_outputs import (
    AudienceSelectionOutput,
    OfferRecommendationOutput,
    CampaignCopyOutput,
    ExperimentMetricsOutput,
)


def test_customer_agent_filtering_and_schema():
    """Verifies CustomerAgent filtering and AudienceSelectionOutput construction."""
    agent = CustomerAgent()
    customers = [
        CustomerModel(
            id="c1", merchant_id="m1", name="Rahul", email="rahul@example.com",
            total_spend_amount=12000.0, total_orders_count=6,
            customer_segment="VIP Dormant", churn_risk_score=0.75,
            predicted_lifetime_value=25000.0,
        ),
        CustomerModel(
            id="c2", merchant_id="m1", name="Ananya", email="ananya@example.com",
            total_spend_amount=2000.0, total_orders_count=1,
            customer_segment="Standard", churn_risk_score=0.20,
            predicted_lifetime_value=4000.0,
        ),
    ]

    dormant = agent.filter_dormant_high_value_customers(customers)
    assert len(dormant) == 1
    assert dormant[0].id == "c1"

    output = agent.build_structured_audience("opp_1", "VIP Dormant", dormant)
    assert isinstance(output, AudienceSelectionOutput)
    assert output.total_audience_count == 1
    assert output.target_customers[0].customer_id == "c1"


def test_offer_agent_tiers_and_schema():
    """Verifies OfferAgent selects appropriate offers and handles VIP upgrades."""
    agent = OfferAgent()

    # Standard VIP Dormant offer
    offer_std = agent.determine_optimal_offer("VIP Dormant", average_spend=5000.0)
    assert isinstance(offer_std, OfferRecommendationOutput)
    assert offer_std.discount_value == 15.0

    # High-spend VIP upgrade
    offer_vip = agent.determine_optimal_offer("VIP Dormant", average_spend=9500.0)
    assert offer_vip.discount_value == 20.0
    assert offer_vip.offer_code == "VIP20OFF"

    # Payment optimization offer
    offer_pay = agent.determine_optimal_offer("payment_optimization", average_spend=3000.0)
    assert offer_pay.offer_code == "UPISWIFT"
    assert "UPI" in offer_pay.description


def test_campaign_agent_copy_and_schema():
    """Verifies CampaignAgent outputs valid CampaignCopyOutput schema."""
    agent = CampaignAgent()
    copy = agent.compose_reengagement_email(
        customer_name="Pooja",
        offer_description="15% Off with code VIP15OFF",
        urgency="Expires in 7 days",
        favorite_category="Footwear",
    )
    assert isinstance(copy, CampaignCopyOutput)
    assert "Pooja" in copy.subject
    assert copy.template_type == "reengagement"

    pay_copy = agent.compose_payment_recovery_copy(
        customer_name="Karan",
        offer_description="₹50 instant checkout rebate",
    )
    assert "UPI" in pay_copy.subject
    assert "retry" in pay_copy.email_body


def test_experiment_agent_metrics_edge_cases():
    """Verifies ExperimentAgent calculates normalized conversion lift and absolute pp difference."""
    agent = ExperimentAgent()

    # Zero conversions edge case
    zero_metrics = agent.calculate_experiment_metrics(
        treatment_conversions=0, treatment_total=100,
        control_conversions=0, control_total=25,
    )
    assert isinstance(zero_metrics, ExperimentMetricsOutput)
    assert zero_metrics.treatment_conversion_rate == 0.0
    assert zero_metrics.incremental_orders_count == 0

    # Positive lift case with normalized derivation
    metrics = agent.calculate_experiment_metrics(
        treatment_conversions=10, treatment_total=100,
        control_conversions=1, control_total=25,
        average_order_value=2000.0,
    )
    assert metrics.treatment_conversion_rate == 0.10
    assert metrics.control_conversion_rate == 0.04
    assert metrics.absolute_difference_percentage == 6.0
    assert metrics.conversion_lift_percentage == 150.0
    assert metrics.incremental_orders_count == 6  # 10 - (100 * 0.04) = 6
    assert metrics.incremental_revenue_inr == 12000.0

    # Zero control conversion case (safeguard against division by zero)
    zero_control_metrics = agent.calculate_experiment_metrics(
        treatment_conversions=29, treatment_total=100,
        control_conversions=0, control_total=25,
        average_order_value=688.0,
    )
    assert zero_control_metrics.control_conversion_rate == 0.0
    assert zero_control_metrics.absolute_difference_percentage == 29.0
    assert zero_control_metrics.relative_lift_display == "N/A (control = 0%)"
    assert zero_control_metrics.conversion_lift_percentage is None
    assert zero_control_metrics.incremental_orders_count == 29


@pytest.mark.anyio
async def test_campaign_dispatcher_wires_offer_agent_recommendation():
    """Verifies that CampaignDispatcher issues coupon matching the exact computed Offer recommendation."""
    from app.actions.campaign_dispatcher import campaign_dispatcher
    from app.actions.discount_coupon_service import discount_coupon_service

    target_customers = [
        {"name": "Sneha", "email": "sneha@example.com", "favorite_category": "Apparel"}
    ]
    offer_code = "VIP25PROMO"
    discount_type = "fixed"
    discount_value = 250.0
    min_order_value = 1500.0

    dispatched = await campaign_dispatcher.execute_email_campaign(
        target_customers=target_customers,
        offer_code=offer_code,
        offer_description="₹250 off on orders above ₹1500",
        discount_type=discount_type,
        discount_value=discount_value,
        min_order_value=min_order_value,
    )
    assert dispatched == 1

    registered_coupon = discount_coupon_service.validate_coupon(offer_code)
    assert registered_coupon is not None
    assert registered_coupon["discount_type"] == "fixed"
    assert registered_coupon["discount_value"] == 250.0
    assert registered_coupon["min_order_value"] == 1500.0

