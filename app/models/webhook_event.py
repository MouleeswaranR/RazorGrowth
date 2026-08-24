from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class WebhookEventModel(Base):
    """Stores raw incoming Razorpay webhook payloads and signature verification status."""

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_name: Mapped[str] = mapped_column(String(100), index=True)
    razorpay_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
