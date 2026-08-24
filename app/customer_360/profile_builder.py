"""Recomputes and synchronizes unified Customer 360 profile metrics and behavioral tags."""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import CustomerModel
from app.customer_360.metric_calculator import calculate_customer_order_metrics
from app.intelligence.customer_segmentation import classify_customer_segment
from app.intelligence.churn_predictor import calculate_churn_risk_with_orders
from app.intelligence.clv_estimator import estimate_customer_lifetime_value
from app.intelligence.distribution_thresholds import compute_merchant_distribution_thresholds


async def refresh_customer_360_profile(session: AsyncSession, customer_id: str) -> CustomerModel | None:
    """Recomputes and persists unified Customer 360 attributes, RFM segment, and churn score."""
    query = (
        select(CustomerModel)
        .options(selectinload(CustomerModel.orders))
        .where(CustomerModel.id == customer_id)
    )
    result = await session.execute(query)
    customer = result.scalar_one_or_none()

    if not customer:
        return None

    metrics = calculate_customer_order_metrics(customer.orders)
    customer.total_orders_count = metrics["total_orders_count"]
    customer.total_spend_amount = metrics["total_spend_amount"]
    customer.last_purchase_timestamp = metrics["last_purchase_timestamp"]

    # Score against this merchant's own spend/recency distribution rather than static
    # defaults, so segmentation stays consistent with the opportunity detectors.
    peers = (await session.execute(
        select(CustomerModel).where(CustomerModel.merchant_id == customer.merchant_id)
    )).scalars().all()
    thresholds = compute_merchant_distribution_thresholds(list(peers))

    customer.customer_segment = classify_customer_segment(customer, thresholds)
    customer.churn_risk_score = calculate_churn_risk_with_orders(
        customer, list(customer.orders), thresholds
    )
    customer.predicted_lifetime_value = estimate_customer_lifetime_value(customer)

    await session.commit()
    return customer
