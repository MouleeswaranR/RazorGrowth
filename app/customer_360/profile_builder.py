from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import CustomerModel
from app.customer_360.metric_calculator import calculate_customer_order_metrics


async def refresh_customer_360_profile(session: AsyncSession, customer_id: str) -> CustomerModel | None:
    """Recomputes and persists unified Customer 360 attributes for a single customer."""
    query = select(CustomerModel).where(CustomerModel.id == customer_id)
    result = await session.execute(query)
    customer = result.scalar_one_or_none()

    if not customer:
        return None

    metrics = calculate_customer_order_metrics(customer.orders)
    customer.total_orders_count = metrics["total_orders_count"]
    customer.total_spend_amount = metrics["total_spend_amount"]
    customer.last_purchase_timestamp = metrics["last_purchase_timestamp"]

    await session.commit()
    return customer
