from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class PaymentModel(Base):
    """Represents a payment transaction lifecycle event linked to Razorpay."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("orders.id"), index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[str] = mapped_column(String(50), default="captured")
    error_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    order = relationship("OrderModel", back_populates="payments")
