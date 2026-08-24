from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class CustomerModel(Base):
    """Represents customer profile, aggregate behavior metrics, and predictive scoring."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Aggregated Customer 360 attributes
    total_orders_count: Mapped[int] = mapped_column(Integer, default=0)
    total_spend_amount: Mapped[float] = mapped_column(Float, default=0.0)
    last_purchase_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    favorite_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Predictive Intelligence attributes
    customer_segment: Mapped[str] = mapped_column(String(50), default="New")
    churn_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_lifetime_value: Mapped[float] = mapped_column(Float, default=0.0)
    repurchase_probability: Mapped[float] = mapped_column(Float, default=0.5)

    merchant = relationship("MerchantModel", back_populates="customers")
    orders = relationship("OrderModel", back_populates="customer", lazy="selectin")
