from app.schemas.agent_outputs import (
    ApprovalStatus,
    PermissionGateResult,
    OfferRecommendationOutput,
    AudienceSelectionOutput,
)


class PermissionGateService:
    """Enforces dynamic merchant safety policies and approval guardrails based on store telemetry."""

    def calculate_dynamic_thresholds(
        self,
        total_customers: int = 500,
        total_gmv: float = 100000.0,
        average_spend: float = 2500.0,
        target_segment: str = "VIP Dormant",
    ) -> dict[str, float]:
        """Calculates dynamic guardrail boundaries tailored to the merchant's live metrics."""
        # VIP and high-value cohorts qualify for higher re-acquisition discount thresholds
        if "VIP" in target_segment or average_spend >= 5000.0:
            max_discount = 25.0
        elif average_spend < 2000.0:
            max_discount = 15.0
        else:
            max_discount = 20.0

        # Safe audience cap dynamically scales with merchant customer volume (up to 25% of total base)
        max_audience = max(25, min(250, int(total_customers * 0.25)))

        # Dynamic campaign dispatch budget cap (up to 3% of store GMV)
        max_budget = max(500.0, min(10000.0, total_gmv * 0.03))

        return {
            "max_discount_percentage": max_discount,
            "max_auto_audience": float(max_audience),
            "max_budget_inr": max_budget,
        }

    def evaluate_campaign_safety(
        self,
        offer: OfferRecommendationOutput,
        audience: AudienceSelectionOutput,
        total_customers: int = 500,
        total_gmv: float = 100000.0,
    ) -> PermissionGateResult:
        """Evaluates whether an autonomous campaign is safe or requires merchant confirmation."""
        avg_spend = (
            sum(c.total_spend for c in audience.target_customers) / max(1, audience.total_audience_count)
        )
        thresholds = self.calculate_dynamic_thresholds(
            total_customers=total_customers,
            total_gmv=total_gmv,
            average_spend=avg_spend,
            target_segment=audience.target_segment,
        )

        max_discount = thresholds["max_discount_percentage"]
        max_audience = int(thresholds["max_auto_audience"])
        estimated_cost = audience.total_audience_count * 2.5

        if offer.discount_type == "percentage" and offer.discount_value > max_discount:
            return PermissionGateResult(
                status=ApprovalStatus.REQUIRES_MERCHANT_APPROVAL,
                is_executable=False,
                policy_notes=(
                    f"Offer discount of {offer.discount_value}% exceeds dynamically calculated limit "
                    f"of {max_discount}% for segment '{audience.target_segment}'. Requires merchant approval."
                ),
                max_allowed_discount_percentage=max_discount,
                estimated_cost_inr=estimated_cost,
            )

        if audience.total_audience_count > max_audience:
            return PermissionGateResult(
                status=ApprovalStatus.REQUIRES_MERCHANT_APPROVAL,
                is_executable=False,
                policy_notes=(
                    f"Audience size of {audience.total_audience_count} customers exceeds dynamic auto-approval "
                    f"cap of {max_audience} (25% of active customer base). Merchant confirmation required."
                ),
                max_allowed_discount_percentage=max_discount,
                estimated_cost_inr=estimated_cost,
            )

        return PermissionGateResult(
            status=ApprovalStatus.AUTO_APPROVED,
            is_executable=True,
            policy_notes=f"Within dynamic guardrails (Max Discount: {max_discount}%, Audience Cap: {max_audience}).",
            max_allowed_discount_percentage=max_discount,
            estimated_cost_inr=estimated_cost,
        )


permission_gate_service = PermissionGateService()
