from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

# Statuses that represent money actually received. Orders outside this set (notably
# "pending_checkout" sessions created for A/B cohorts) must never count toward
# customer spend, recency, or merchant GMV.
PAID_ORDER_STATUSES: tuple[str, ...] = ("completed", "paid")


class OrderModel(Base):
    """Represents an order placed by a customer linked to Razorpay test orders."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), index=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[str] = mapped_column(String(50), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    customer = relationship("CustomerModel", back_populates="orders")
    product = relationship("ProductModel", back_populates="orders")
    payments = relationship("PaymentModel", back_populates="order", lazy="selectin")
