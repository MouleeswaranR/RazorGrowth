from app.services.permission_gate_service import permission_gate_service
from app.schemas.agent_outputs import (
    ApprovalStatus,
    OfferRecommendationOutput,
    AudienceSelectionOutput,
)


def test_permission_gate_dynamic_threshold_calculation():
    """Verifies dynamic calculation of thresholds based on merchant customer count and spend."""
    # VIP cohort with high spend
    vip_thresholds = permission_gate_service.calculate_dynamic_thresholds(
        total_customers=1000,
        total_gmv=500000.0,
        average_spend=6000.0,
        target_segment="VIP Dormant",
    )
    assert vip_thresholds["max_discount_percentage"] == 25.0
    assert vip_thresholds["max_auto_audience"] == 250.0

    # Low spend cohort
    low_thresholds = permission_gate_service.calculate_dynamic_thresholds(
        total_customers=100,
        total_gmv=20000.0,
        average_spend=1200.0,
        target_segment="Standard",
    )
    assert low_thresholds["max_discount_percentage"] == 15.0
    assert low_thresholds["max_auto_audience"] == 25.0


def test_permission_gate_requires_approval_for_excessive_discount():
    """Verifies that an offer exceeding dynamic maximum discount triggers merchant approval."""
    offer_excessive = OfferRecommendationOutput(
        offer_code="VIP50OFF",
        discount_type="percentage",
        discount_value=50.0,  # Exceeds dynamic max 25%
        min_order_value=1000.0,
        description="50% off",
        urgency_text="Today only",
    )
    audience = AudienceSelectionOutput(
        opportunity_id="opp_1",
        target_segment="VIP Dormant",
        total_audience_count=50,
    )

    decision = permission_gate_service.evaluate_campaign_safety(
        offer=offer_excessive,
        audience=audience,
        total_customers=500,
        total_gmv=100000.0,
    )
    assert decision.status == ApprovalStatus.REQUIRES_MERCHANT_APPROVAL
    assert decision.is_executable is False
    assert "exceeds" in decision.policy_notes


def test_permission_gate_requires_approval_for_large_audience():
    """Verifies that large audience triggers merchant approval."""
    offer_safe = OfferRecommendationOutput(
        offer_code="VIP15OFF",
        discount_type="percentage",
        discount_value=15.0,
        min_order_value=1000.0,
        description="15% off",
        urgency_text="7 days",
    )
    audience_large = AudienceSelectionOutput(
        opportunity_id="opp_1",
        target_segment="VIP Dormant",
        total_audience_count=500,  # Exceeds dynamic cap (max 125 for 500 customers)
    )

    decision = permission_gate_service.evaluate_campaign_safety(
        offer=offer_safe,
        audience=audience_large,
        total_customers=500,
        total_gmv=100000.0,
    )
    assert decision.status == ApprovalStatus.REQUIRES_MERCHANT_APPROVAL
    assert decision.is_executable is False


def test_permission_gate_auto_approves_safe_campaign():
    """Verifies that safe discounts with manageable audience sizes are auto-approved."""
    offer_safe = OfferRecommendationOutput(
        offer_code="VIP15OFF",
        discount_type="percentage",
        discount_value=15.0,
        min_order_value=1000.0,
        description="15% off",
        urgency_text="7 days",
    )
    audience_safe = AudienceSelectionOutput(
        opportunity_id="opp_1",
        target_segment="VIP Dormant",
        total_audience_count=40,
    )

    decision = permission_gate_service.evaluate_campaign_safety(
        offer=offer_safe,
        audience=audience_safe,
        total_customers=500,
        total_gmv=100000.0,
    )
    assert decision.status == ApprovalStatus.AUTO_APPROVED
    assert decision.is_executable is True
