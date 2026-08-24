import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.experiment_order_creator import experiment_order_creator
from app.services.webhook_payment_processor import webhook_payment_processor
from app.services.experiment_metrics_calculator import experiment_metrics_calculator

logger = logging.getLogger(__name__)


class LiveExperimentService:
    """Coordinates experiment lifecycle: order creation, webhook processing, and metrics calculation."""

    async def create_cohort_test_orders(
        self,
        session: AsyncSession,
        campaign_id: str,
        treatment_customers: list[dict],
        control_customers: list[dict],
        merchant_id: str,
        offer_amount: float,
        session_id: str | None = None,
    ) -> list[dict]:
        """Creates Razorpay test orders for treatment cohort and records experiment assignments."""
        return await experiment_order_creator.create_cohort_test_orders(
            session=session,
            campaign_id=campaign_id,
            treatment_customers=treatment_customers,
            control_customers=control_customers,
            merchant_id=merchant_id,
            offer_amount=offer_amount,
            session_id=session_id,
        )

    async def record_webhook_payment(
        self,
        session: AsyncSession,
        event_payload: dict,
    ) -> dict:
        """Processes webhook payment event and refreshes Customer 360."""
        result = await webhook_payment_processor.record_webhook_payment(
            session=session,
            event_payload=event_payload,
        )

        # Recalculate metrics if campaign_id is present
        if result.get("campaign_id"):
            return await self.recalculate_campaign_metrics(
                session=session,
                campaign_id=result["campaign_id"],
                session_id=result.get("session_id"),
            )

        return result

    async def recalculate_campaign_metrics(
        self,
        session: AsyncSession,
        campaign_id: str,
        session_id: str | None = None,
    ) -> dict:
        """Calculates conversion rates and incremental lift from experiment assignments."""
        return await experiment_metrics_calculator.recalculate_campaign_metrics(
            session=session,
            campaign_id=campaign_id,
            session_id=session_id,
        )


live_experiment_service = LiveExperimentService()
