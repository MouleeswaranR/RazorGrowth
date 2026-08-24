from datetime import datetime
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ExperimentAssignmentModel(Base):
    """Tracks customer variant assignments and conversion outcomes for A/B experiments."""

    __tablename__ = "experiment_assignments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), index=True)
    variant: Mapped[str] = mapped_column(String(20), default="treatment", index=True)
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    conversion_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conversion_amount: Mapped[float] = mapped_column(Float, default=0.0)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer = relationship("CustomerModel", lazy="selectin")
    campaign = relationship("CampaignModel", lazy="selectin")
