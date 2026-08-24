from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_database_session
from app.models.customer import CustomerModel

router = APIRouter(prefix="/customers", tags=["Customer 360"])


@router.get("/")
async def list_customers(
    merchant_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_database_session),
) -> list[dict]:
    """Retrieves paginated Customer 360 profiles for a merchant."""
    query = select(CustomerModel).where(CustomerModel.merchant_id == merchant_id).limit(limit)
    result = await session.execute(query)
    customers = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "total_orders": c.total_orders_count,
            "total_spend": c.total_spend_amount,
            "segment": c.customer_segment,
            "churn_risk": c.churn_risk_score,
            "clv": c.predicted_lifetime_value,
        }
        for c in customers
    ]


@router.get("/{customer_id}")
async def get_customer_details(
    customer_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Fetches full Customer 360 detail record by unique ID."""
    query = select(CustomerModel).where(CustomerModel.id == customer_id)
    result = await session.execute(query)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "location": customer.location,
        "segment": customer.customer_segment,
        "total_spend": customer.total_spend_amount,
        "total_orders": customer.total_orders_count,
    }
