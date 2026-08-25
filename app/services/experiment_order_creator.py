import uuid
import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import OrderModel
from app.models.product import ProductModel
from app.models.experiment_assignment import ExperimentAssignmentModel

logger = logging.getLogger(__name__)


class ExperimentOrderCreator:
    """Handles Razorpay test order creation for experiment treatment and control cohorts."""

    async def create_cohort_test_orders(
        self,
        session: AsyncSession,
        campaign_id: str,
        treatment_customers: list[dict],
        control_customers: list[dict],
        merchant_id: str,
        treatment_amount: float,
        control_amount: float,
        session_id: str | None = None,
    ) -> list[dict]:
        """Creates Razorpay test orders for treatment cohort and records initial experiment assignments."""
        from app.integrations.razorpay_client import razorpay_client

        treatment_amount = round(float(treatment_amount), 2)
        control_amount = round(float(control_amount), 2)
        prod_id = await self._ensure_product_exists(session, merchant_id, control_amount)

        checkout_sessions = []
        orders_to_create = []
        assignments_to_create = []

        cohorts = (("treatment", treatment_customers), ("control", control_customers))
        for variant, customers in cohorts:
            for idx, c in enumerate(customers):
                cust_id = c.get("id") or c.get("customer_id")
                checkout_amount = treatment_amount if variant == "treatment" else control_amount
                amount_in_paise = max(100, int(checkout_amount * 100))
                notes = {
                    "campaign_id": str(campaign_id),
                    "customer_id": str(cust_id),
                    "variant": variant,
                    "session_id": str(session_id or ""),
                }

                rzp_order_id = None
                is_mock_order = False
                try:
                    rzp_order = razorpay_client.create_order(
                        amount_in_paise=amount_in_paise,
                        receipt=f"rcpt_{variant}_{cust_id[:8]}",
                        notes=notes,
                    )
                    rzp_order_id = rzp_order.get("id")
                    is_mock_order = bool(rzp_order.get("is_mock", False))
                    if idx < 10:
                        await asyncio.sleep(0.06)
                except Exception as rzp_err:
                    logger.warning(f"Razorpay order creation fallback: {rzp_err}")
                    rzp_order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
                    is_mock_order = True

                order_id = f"ord_{uuid.uuid4().hex[:12]}"
                orders_to_create.append(OrderModel(
                    id=order_id,
                    merchant_id=merchant_id,
                    customer_id=cust_id,
                    product_id=prod_id,
                    razorpay_order_id=rzp_order_id,
                    amount=checkout_amount,
                    status="pending_checkout",
                ))
                assignments_to_create.append(ExperimentAssignmentModel(
                    id=f"asgn_{uuid.uuid4().hex[:12]}",
                    campaign_id=campaign_id,
                    customer_id=cust_id,
                    variant=variant,
                    razorpay_order_id=rzp_order_id,
                    is_converted=False,
                    conversion_amount=0.0,
                ))
                checkout_sessions.append({
                    "order_id": order_id,
                    "razorpay_order_id": rzp_order_id,
                    "customer_id": cust_id,
                    "customer_name": c.get("name", "Merchant Customer"),
                    "customer_email": c.get("email", "customer@example.com"),
                    "amount": checkout_amount,
                    "variant": variant,
                    "is_mock": is_mock_order,
                })

        if orders_to_create:
            session.add_all(orders_to_create)
        if assignments_to_create:
            session.add_all(assignments_to_create)

        await session.commit()
        return checkout_sessions

    async def _ensure_product_exists(
        self,
        session: AsyncSession,
        merchant_id: str,
        offer_amount: float,
    ) -> str:
        """Ensures a product exists for the merchant, creating one if necessary."""
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
        return prod_id


experiment_order_creator = ExperimentOrderCreator()
