import uuid
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.models.customer import CustomerModel
from app.models.merchant import MerchantModel
from app.models.product import ProductModel
from app.models.webhook_event import WebhookEventModel
from app.models.experiment_assignment import ExperimentAssignmentModel

logger = logging.getLogger(__name__)


class WebhookPaymentProcessor:
    """Processes Razorpay webhook payment events and updates experiment assignments."""

    async def record_webhook_payment(
        self,
        session: AsyncSession,
        event_payload: dict,
    ) -> dict:
        """Processes real webhook payment event, records order payment, refreshes Customer 360, and returns campaign_id."""
        from app.customer_360.profile_builder import refresh_customer_360_profile

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
        order = await self._get_or_create_order(
            session, order_id, customer_id, amount
        )

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
            await self._update_experiment_assignment(
                session, campaign_id, customer_id, order.id, amount
            )

        await session.commit()

        # Refresh Customer 360 profile
        target_cust_id = customer_id or (order.customer_id if order else None)
        if target_cust_id:
            try:
                await refresh_customer_360_profile(session, target_cust_id)
            except Exception as refresh_err:
                logger.warning(f"Customer 360 profile refresh error: {refresh_err}")

        return {
            "status": "payment_recorded",
            "payment_id": payment_id,
            "campaign_id": campaign_id,
            "session_id": event_payload.get("session_id"),
        }

    async def _get_or_create_order(
        self,
        session: AsyncSession,
        order_id: str,
        customer_id: str,
        amount: float,
    ) -> OrderModel:
        """Gets existing order or creates a new one if not found."""
        order_stmt = select(OrderModel).where(
            (OrderModel.razorpay_order_id == order_id) | (OrderModel.id == order_id)
        )
        order = (await session.execute(order_stmt)).scalar_one_or_none()

        if not order:
            merchant_id = await self._ensure_merchant_exists(session)
            existing_cust_id = await self._ensure_customer_exists(
                session, customer_id, merchant_id
            )
            existing_prod_id = await self._ensure_product_exists(
                session, merchant_id, amount
            )

            order = OrderModel(
                id=f"ord_{uuid.uuid4().hex[:12]}",
                merchant_id=merchant_id,
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

        return order

    async def _ensure_merchant_exists(self, session: AsyncSession) -> str:
        """Ensures a default merchant exists."""
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
        return existing_merchant_id

    async def _ensure_customer_exists(
        self,
        session: AsyncSession,
        customer_id: str,
        merchant_id: str,
    ) -> str:
        """Ensures customer exists, creating if necessary."""
        cust_stmt = select(CustomerModel.id).where(CustomerModel.id == customer_id)
        existing_cust_id = (await session.execute(cust_stmt)).scalar_one_or_none()
        if not existing_cust_id:
            resolved_id = customer_id or f"cust_{uuid.uuid4().hex[:10]}"
            logger.warning(
                f"Customer '{customer_id}' not found. Creating record '{resolved_id}'."
            )
            new_cust = CustomerModel(
                id=resolved_id,
                merchant_id=merchant_id,
                name="Recovered Customer",
                email="customer@example.com",
            )
            session.add(new_cust)
            await session.flush()
            existing_cust_id = new_cust.id
        return existing_cust_id

    async def _ensure_product_exists(
        self,
        session: AsyncSession,
        merchant_id: str,
        amount: float,
    ) -> str:
        """Ensures product exists, creating if necessary."""
        prod_stmt = select(ProductModel.id).where(
            ProductModel.merchant_id == merchant_id
        )
        existing_prod_id = (await session.execute(prod_stmt)).scalars().first()
        if not existing_prod_id:
            new_prod = ProductModel(
                id=f"prod_{uuid.uuid4().hex[:10]}",
                merchant_id=merchant_id,
                title="Recovered Product",
                category="General",
                price=amount,
            )
            session.add(new_prod)
            await session.flush()
            existing_prod_id = new_prod.id
        return existing_prod_id

    async def _update_experiment_assignment(
        self,
        session: AsyncSession,
        campaign_id: str,
        customer_id: str,
        order_id: str,
        amount: float,
    ) -> None:
        """Updates experiment assignment with conversion details."""
        asgn_stmt = select(ExperimentAssignmentModel).where(
            ExperimentAssignmentModel.campaign_id == campaign_id,
            ExperimentAssignmentModel.customer_id == customer_id,
        )
        asgn = (await session.execute(asgn_stmt)).scalar_one_or_none()
        if asgn:
            asgn.is_converted = True
            asgn.conversion_order_id = order_id
            asgn.conversion_amount = amount
            asgn.converted_at = datetime.utcnow()
        else:
            logger.warning(
                f"No assignment found for campaign '{campaign_id}' "
                f"and customer '{customer_id}'."
            )


webhook_payment_processor = WebhookPaymentProcessor()
