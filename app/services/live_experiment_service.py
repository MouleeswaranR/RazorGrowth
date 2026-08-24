import uuid
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import CampaignModel
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.models.customer import CustomerModel
from app.models.merchant import MerchantModel
from app.models.product import ProductModel
from app.models.webhook_event import WebhookEventModel
from app.models.experiment_assignment import ExperimentAssignmentModel
from app.agents.experiment_agent import ExperimentAgent
from app.services.trace_logger_service import trace_logger_service

logger = logging.getLogger(__name__)


class LiveExperimentService:
    """Manages real Razorpay test order creation, live webhook processing, and metric recalculation."""

    def __init__(self) -> None:
        """Initializes the experiment calculation agent."""
        self._experiment_agent = ExperimentAgent()

    async def create_cohort_test_orders(
        self,
        session: AsyncSession,
        campaign_id: str,
        merchant_id: str,
        treatment_customers: list,
        control_customers: list,
        offer_amount: float,
        session_id: str | None = None,
    ) -> list[dict]:
        """Creates pending test order records in PostgreSQL and returns checkout payload."""
        from app.integrations.razorpay_client import razorpay_client

        offer_amount = round(float(offer_amount), 2)
        prod_stmt = select(ProductModel.id).where(ProductModel.merchant_id == merchant_id)
        prod_id = (await session.execute(prod_stmt)).scalars().first()
        if not prod_id:
            new_prod = ProductModel(
                id=f"prod_{uuid.uuid4().hex[:10]}",
                merchant_id=merchant_id,
                title="Special Offer Item",
                category="General",
                price=offer_amount,
            )
            session.add(new_prod)
            await session.flush()
            prod_id = new_prod.id

        checkout_sessions = []
        orders_to_create = []
        assignments_to_create = []

        # Process Treatment Cohort (Assigned + Razorpay Test Orders)
        for c in treatment_customers:
            cust_id = c.get("id") or c.get("customer_id")
            amount_in_paise = max(100, int(offer_amount * 100))
            notes = {
                "campaign_id": str(campaign_id),
                "customer_id": str(cust_id),
                "variant": "treatment",
                "session_id": str(session_id or ""),
            }
            rzp_order = razorpay_client.create_order(
                amount_in_paise=amount_in_paise,
                receipt=f"rcpt_{cust_id[:8]}",
                notes=notes,
            )
            order_id = f"ord_{uuid.uuid4().hex[:12]}"
            order = OrderModel(
                id=order_id,
                merchant_id=merchant_id,
                customer_id=cust_id,
                product_id=prod_id,
                razorpay_order_id=rzp_order.get("id"),
                amount=offer_amount,
                status="pending_checkout",
            )
            orders_to_create.append(order)

            assignment = ExperimentAssignmentModel(
                id=f"asgn_{uuid.uuid4().hex[:12]}",
                campaign_id=campaign_id,
                customer_id=cust_id,
                variant="treatment",
                is_converted=False,
                conversion_amount=0.0,
            )
            assignments_to_create.append(assignment)

            checkout_sessions.append({
                "order_id": order_id,
                "razorpay_order_id": rzp_order.get("id"),
                "customer_id": cust_id,
                "customer_name": c.get("name", "Merchant Customer"),
                "customer_email": c.get("email", "customer@example.com"),
                "amount": offer_amount,
                "variant": "treatment",
            })

        # Process Control Cohort (Assigned baseline)
        for c in control_customers:
            cust_id = c.get("id") or c.get("customer_id")
            assignment = ExperimentAssignmentModel(
                id=f"asgn_{uuid.uuid4().hex[:12]}",
                campaign_id=campaign_id,
                customer_id=cust_id,
                variant="control",
                is_converted=False,
                conversion_amount=0.0,
            )
            assignments_to_create.append(assignment)

        if orders_to_create:
            session.add_all(orders_to_create)
        if assignments_to_create:
            session.add_all(assignments_to_create)

        await session.commit()
        return checkout_sessions

    async def record_webhook_payment(
        self,
        session: AsyncSession,
        event_payload: dict,
    ) -> dict:
        """Processes real webhook payment event, records order payment, and recalculates metrics."""
        campaign_id = event_payload.get("campaign_id")
        customer_id = event_payload.get("customer_id")
        amount = event_payload.get("amount", 0.0)
        payment_id = event_payload.get("payment_id") or f"pay_{uuid.uuid4().hex[:12]}"
        order_id = event_payload.get("order_id") or f"ord_{uuid.uuid4().hex[:12]}"

        # Log into webhook_events table in PostgreSQL
        webhook_log = WebhookEventModel(
            id=f"wevt_{uuid.uuid4().hex[:12]}",
            event_name=event_payload.get("event", "payment.captured"),
            razorpay_event_id=payment_id,
            signature_valid=True,
            payload=event_payload,
            status="processed",
        )
        session.add(webhook_log)

        # Ensure associated OrderModel exists in PostgreSQL
        order_stmt = select(OrderModel).where(
            (OrderModel.razorpay_order_id == order_id) | (OrderModel.id == order_id)
        )
        order = (await session.execute(order_stmt)).scalar_one_or_none()

        if not order:
            merchant_stmt = select(MerchantModel.id)
            existing_merchant_id = (await session.execute(merchant_stmt)).scalars().first()
            if not existing_merchant_id:
                first_merch = MerchantModel(
                    id="merch_default",
                    name="Default Merchant",
                    category="E-commerce",
                    currency="INR",
                )
                session.add(first_merch)
                await session.flush()
                existing_merchant_id = "merch_default"


            cust_stmt = select(CustomerModel.id).where(CustomerModel.id == customer_id)
            existing_cust_id = (await session.execute(cust_stmt)).scalar_one_or_none()
            if not existing_cust_id:
                resolved_id = customer_id or f"cust_{uuid.uuid4().hex[:10]}"
                logger.warning(
                    f"Customer '{customer_id}' not found in database during webhook processing. "
                    f"Creating dedicated record '{resolved_id}'."
                )
                new_cust = CustomerModel(
                    id=resolved_id,
                    merchant_id=existing_merchant_id,
                    name="Recovered Customer",
                    email="customer@example.com",
                )
                session.add(new_cust)
                await session.flush()
                existing_cust_id = new_cust.id

            prod_stmt = select(ProductModel.id).where(ProductModel.merchant_id == existing_merchant_id)
            existing_prod_id = (await session.execute(prod_stmt)).scalars().first()
            if not existing_prod_id:
                new_prod = ProductModel(
                    id=f"prod_{uuid.uuid4().hex[:10]}",
                    merchant_id=existing_merchant_id,
                    title="Recovered Product",
                    category="General",
                    price=amount,
                )
                session.add(new_prod)
                await session.flush()
                existing_prod_id = new_prod.id

            order = OrderModel(
                id=f"ord_{uuid.uuid4().hex[:12]}",
                merchant_id=existing_merchant_id,
                customer_id=existing_cust_id,
                product_id=existing_prod_id,
                razorpay_order_id=order_id,
                amount=amount,
                status="paid",
            )
            session.add(order)
            await session.flush()
        else:
            order.status = "paid"

        # Upsert payment record linked to order.id
        payment = PaymentModel(
            id=f"pay_{uuid.uuid4().hex[:12]}",
            order_id=order.id,
            razorpay_payment_id=payment_id,
            amount=amount,
            payment_method=event_payload.get("method", "upi"),
            status="captured",
        )
        session.add(payment)

        # Update experiment assignment conversion in PostgreSQL
        if campaign_id:
            asgn_stmt = select(ExperimentAssignmentModel).where(
                ExperimentAssignmentModel.campaign_id == campaign_id,
                ExperimentAssignmentModel.customer_id == customer_id,
            )
            asgn = (await session.execute(asgn_stmt)).scalar_one_or_none()
            if asgn:
                asgn.is_converted = True
                asgn.conversion_order_id = order.id
                asgn.conversion_amount = amount
                asgn.converted_at = datetime.utcnow()
            else:
                logger.warning(
                    f"[Experiment Attribution Alert] No assignment found for campaign '{campaign_id}' "
                    f"and customer '{customer_id}'. Conversion logged without variant attribution."
                )

        await session.commit()

        if campaign_id:
            return await self.recalculate_campaign_metrics(session, campaign_id, event_payload.get("session_id"))

        return {"status": "payment_recorded", "payment_id": payment_id}

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

        treatment_conversions = sum(1 for a in treatment_cohort if a.is_converted)
        treatment_total = max(1, len(treatment_cohort))
        control_conversions = sum(1 for a in control_cohort if a.is_converted)
        control_total = max(1, len(control_cohort))

        # If no assignments found in table, return explicit sentinel zero-data state
        if not assignments:
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

        campaign.treatment_conversion_rate = metrics.treatment_conversion_rate
        campaign.control_conversion_rate = metrics.control_conversion_rate
        campaign.incremental_revenue_generated = metrics.incremental_revenue_inr
        campaign.status = "measured_live"
        await session.commit()

        converted_customers_list = []
        for a in treatment_cohort:
            if a.is_converted:
                cust_name = a.customer.name if a.customer else "Recovered Customer"
                converted_customers_list.append({
                    "customer_name": cust_name,
                    "customer_id": a.customer_id,
                    "amount_paid": a.conversion_amount,
                    "razorpay_order_id": a.conversion_order_id,
                    "variant": a.variant,
                    "converted_at": a.converted_at.isoformat() if a.converted_at else None,
                })

        # Update trace logger under merchant_id and session_id
        step_payload = {
            "campaign_id": campaign_id,
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
        # Store episodic memory record in VectorMemoryService
        from app.services.vector_memory_service import vector_memory_service
        memory_summary = (
            f"Campaign '{campaign.name}' achieved {metrics.relative_lift_display} lift, "
            f"+{metrics.incremental_orders_count} incremental order(s), and "
            f"₹{metrics.incremental_revenue_inr:,.0f} net incremental GMV measured via Razorpay Webhooks."
        )
        vector_memory_service.store_memory(
            memory_id=f"mem_outcome_{campaign_id}",
            merchant_id=session_id or "merch_default",
            memory_type="campaign_outcome",
            summary_text=memory_summary,
            metadata={
                "campaign_id": campaign_id,
                "incremental_gmv": float(metrics.incremental_revenue_inr),
                "incremental_orders": int(metrics.incremental_orders_count),
                "treatment_rate": float(metrics.treatment_conversion_rate),
                "control_rate": float(metrics.control_conversion_rate),
            },
        )

        return metrics.model_dump()


live_experiment_service = LiveExperimentService()
