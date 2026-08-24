from app.actions.message_simulator import message_simulator
from app.actions.discount_coupon_service import discount_coupon_service
from app.agents.campaign_agent import CampaignAgent


class CampaignDispatcher:
    """Executes multi-channel campaign dispatch to targeted customer cohorts."""

    def __init__(self) -> None:
        """Initializes Campaign Agent dependency."""
        self._campaign_agent = CampaignAgent()

    async def execute_email_campaign(
        self,
        target_customers: list[dict],
        offer_code: str,
        offer_description: str,
        discount_type: str = "percentage",
        discount_value: float = 15.0,
        min_order_value: float = 0.0,
        campaign_type: str = "general",
        use_ai_copy: bool = False,
    ) -> int:
        """Issues coupon with exact computed discount terms and dispatches opportunity-aligned emails."""
        discount_coupon_service.issue_coupon(
            code=offer_code,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_value=min_order_value,
        )
        dispatched_count = 0

        for customer in target_customers:
            name = customer.get("name", "Valued Customer")
            email = customer.get("email", "customer@example.com")
            category = customer.get("favorite_category", "Apparel")

            if use_ai_copy:
                copy = await self._campaign_agent.compose_personalized_copy(
                    customer_name=name,
                    offer_description=offer_description,
                    favorite_category=category,
                )
            elif campaign_type == "payment_optimization":
                copy = self._campaign_agent.compose_payment_recovery_copy(
                    customer_name=name,
                    offer_description=offer_description,
                )
            else:
                copy = self._campaign_agent.compose_personalized_email(
                    customer_name=name,
                    offer_description=offer_description,
                    favorite_category=category,
                )

            message_simulator.dispatch_email(
                recipient_email=email,
                subject=copy.subject,
                body=copy.email_body,
            )
            dispatched_count += 1

        return dispatched_count


campaign_dispatcher = CampaignDispatcher()
