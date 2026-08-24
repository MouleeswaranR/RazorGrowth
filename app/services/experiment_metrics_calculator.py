import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import CampaignModel
from app.models.experiment_assignment import ExperimentAssignmentModel
from app.agents.experiment_agent import ExperimentAgent
from app.services.trace_logger_service import trace_logger_service

logger = logging.getLogger(__name__)


class ExperimentMetricsCalculator:
    """Calculates and stores experiment conversion metrics and lift."""

    def __init__(self) -> None:
        """Initializes the experiment calculation agent."""
        self._experiment_agent = ExperimentAgent()

    async def recalculate_campaign_metrics(
        self,
        session: AsyncSession,
        campaign_id: str,
        session_id: str | None = None,
    ) -> dict:
        """Calculates conversion rates and incremental lift from PostgreSQL experiment assignments."""
        camp_stmt = select(CampaignModel).where(CampaignModel.id == campaign_id)
        campaign = (await session.execute(camp_stmt)).scalar_one_or_none()
        if not campaign:
            return {}

        asgn_stmt = select(ExperimentAssignmentModel).where(
            ExperimentAssignmentModel.campaign_id == campaign_id
        )
        assignments = (await session.execute(asgn_stmt)).scalars().all()

        treatment_cohort = [a for a in assignments if a.variant == "treatment"]
        control_cohort = [a for a in assignments if a.variant == "control"]

        # If no assignments found in table, return explicit sentinel zero-data state
        if not assignments:
            return await self._create_empty_metrics(campaign, session)

        treatment_conversions = sum(1 for a in treatment_cohort if a.is_converted)
        treatment_total = max(1, len(treatment_cohort))
        control_conversions = sum(1 for a in control_cohort if a.is_converted)
        control_total = max(1, len(control_cohort))

        # Calculate actual captured GMV from converted orders
        treatment_converted_amounts = [
            a.conversion_amount for a in treatment_cohort
            if a.is_converted and a.conversion_amount > 0
        ]
        actual_treatment_gmv = sum(treatment_converted_amounts)
        actual_treatment_aov = (
            actual_treatment_gmv / len(treatment_converted_amounts)
        ) if treatment_converted_amounts else 2850.0

        metrics = self._experiment_agent.calculate_experiment_metrics(
            treatment_conversions=treatment_conversions,
            treatment_total=treatment_total,
            control_conversions=control_conversions,
            control_total=control_total,
            average_order_value=actual_treatment_aov,
        )

        # Update campaign with metrics
        campaign.treatment_conversion_rate = metrics.treatment_conversion_rate
        campaign.control_conversion_rate = metrics.control_conversion_rate
        campaign.incremental_revenue_generated = metrics.incremental_revenue_inr
        campaign.status = "measured_live"
        await session.commit()

        # Build converted customers list
        converted_customers_list = self._build_converted_customers_list(treatment_cohort)

        # Log trace and store vector memory
        self._log_experiment_trace(
            campaign, metrics, actual_treatment_gmv,
            treatment_conversions, converted_customers_list, session_id
        )

        self._store_campaign_memory(
            campaign, metrics, session_id
        )

        return metrics.model_dump()

    async def _create_empty_metrics(
        self,
        campaign: CampaignModel,
        session: AsyncSession,
    ) -> dict:
        """Creates empty metrics when no conversions have been recorded."""
        empty_metrics = {
            "treatment_conversion_rate": 0.0,
            "control_conversion_rate": 0.0,
            "conversion_lift_percentage": 0.0,
            "absolute_difference_percentage": 0.0,
            "relative_lift_display": "N/A (no conversions recorded yet)",
            "incremental_orders_count": 0,
            "incremental_revenue_inr": 0.0,
            "status_note": "no_conversions_recorded_yet",
            "treatment_orders_count": 0,
            "treatment_total_count": campaign.target_customer_count,
            "control_orders_count": 0,
            "control_total_count": 0,
        }
        campaign.treatment_conversion_rate = 0.0
        campaign.control_conversion_rate = 0.0
        campaign.incremental_revenue_generated = 0.0
        await session.commit()
        return empty_metrics

    def _build_converted_customers_list(self, treatment_cohort: list) -> list[dict]:
        """Builds list of converted customers with details."""
        converted_customers = []
        for a in treatment_cohort:
            if a.is_converted:
                cust_name = a.customer.name if a.customer else "Recovered Customer"
                converted_customers.append({
                    "customer_name": cust_name,
                    "customer_id": a.customer_id,
                    "amount_paid": a.conversion_amount,
                    "razorpay_order_id": a.conversion_order_id,
                    "variant": a.variant,
                    "converted_at": a.converted_at.isoformat() if a.converted_at else None,
                })
        return converted_customers

    def _log_experiment_trace(
        self,
        campaign: CampaignModel,
        metrics: dict,
        actual_treatment_gmv: float,
        treatment_conversions: int,
        converted_customers_list: list[dict],
        session_id: str | None,
    ) -> None:
        """Logs experiment results to trace logger."""
        step_payload = {
            "campaign_id": campaign.id,
            "opportunity_id": campaign.opportunity_id,
            "metrics": metrics.model_dump(),
            "captured_gmv": round(actual_treatment_gmv, 2),
            "converted_customers": converted_customers_list,
            "experiment_reasoning": (
                f"Real-time metrics measured directly via Razorpay Test Mode Orders and Webhook events. "
                f"Treatment captured GMV: ₹{actual_treatment_gmv:,.2f} across {treatment_conversions} orders."
            ),
            "orders_created": treatment_conversions,
            "measured_via": "Razorpay Test Webhooks",
        }
        trace_logger_service.log_trace_step(
            run_id=campaign.opportunity_id,
            session_id=session_id,
            step_name="4_experiment_ab_lift_measurement",
            step_data=step_payload,
        )

    def _store_campaign_memory(
        self,
        campaign: CampaignModel,
        metrics: dict,
        session_id: str | None,
    ) -> None:
        """Stores campaign outcome in vector memory for future retrieval."""
        from app.services.vector_memory_service import vector_memory_service

        memory_summary = (
            f"Campaign '{campaign.name}' achieved {metrics.relative_lift_display} lift, "
            f"+{metrics.incremental_orders_count} incremental order(s), and "
            f"₹{metrics.incremental_revenue_inr:,.0f} net incremental GMV measured via Razorpay Webhooks."
        )
        vector_memory_service.store_memory(
            memory_id=f"mem_outcome_{campaign.id}",
            merchant_id=session_id or "merch_default",
            memory_type="campaign_outcome",
            summary_text=memory_summary,
            metadata={
                "campaign_id": campaign.id,
                "incremental_gmv": float(metrics.incremental_revenue_inr),
                "incremental_orders": int(metrics.incremental_orders_count),
                "treatment_rate": float(metrics.treatment_conversion_rate),
                "control_rate": float(metrics.control_conversion_rate),
            },
        )


experiment_metrics_calculator = ExperimentMetricsCalculator()
