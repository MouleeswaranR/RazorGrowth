from app.models.customer import CustomerModel
from app.schemas.agent_outputs import AudienceSelectionOutput, CustomerTargetProfile


class CustomerAgent:
    """Filters and segments customer cohorts, returning validated audience manifests with reasoning."""

    def filter_dormant_high_value_customers(
        self,
        customers: list[CustomerModel],
        min_spend_threshold: float = 5000.0,
    ) -> list[CustomerModel]:
        """Identifies high-value customers needing re-engagement campaigns."""
        return [
            c for c in customers
            if c.total_spend_amount >= min_spend_threshold
            and c.customer_segment in ("VIP Dormant", "Loyal At Risk")
        ]

    def filter_active_customers(
        self,
        customers: list[CustomerModel],
    ) -> list[CustomerModel]:
        """Selects active low-churn customers suitable for cross-sell campaigns."""
        return [
            c for c in customers
            if c.churn_risk_score < 0.50
            and c.total_orders_count >= 2
        ]

    def build_structured_audience(
        self,
        opportunity_id: str,
        target_segment: str,
        selected_customers: list[CustomerModel],
    ) -> AudienceSelectionOutput:
        """Constructs a validated AudienceSelectionOutput schema with explicit cohort selection reasoning."""
        profiles = [
            CustomerTargetProfile(
                customer_id=c.id,
                name=c.name,
                email=c.email,
                favorite_category=c.favorite_category or "Apparel",
                segment=c.customer_segment,
                total_spend=round(c.total_spend_amount, 2),
            )
            for c in selected_customers
        ]

        if target_segment == "VIP Dormant":
            reasoning = (
                f"Selected {len(profiles)} high-value customers with >₹5,000 historical spend who have been inactive "
                f"for >30 days to prevent permanent churn."
            )
        elif target_segment == "payment_optimization":
            reasoning = (
                f"Targeted {len(profiles)} active customers experiencing checkout payment friction to re-engage with "
                f"frictionless 1-Click UPI retries."
            )
        else:
            reasoning = (
                f"Identified {len(profiles)} loyal customers with frequent purchase history for category expansion."
            )

        return AudienceSelectionOutput(
            opportunity_id=opportunity_id,
            target_segment=target_segment,
            total_audience_count=len(profiles),
            target_customers=profiles,
            reasoning=reasoning,
        )
