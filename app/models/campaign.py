from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class CampaignModel(Base):
    """Represents an autonomous re-engagement campaign and A/B experiment metrics."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(64), ForeignKey("growth_opportunities.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    offer_details: Mapped[str] = mapped_column(String(255), nullable=False)
    message_copy: Mapped[Text] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")

    target_customer_count: Mapped[int] = mapped_column(Integer, default=0)
    treatment_conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    control_conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    incremental_revenue_generated: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunity = relationship("OpportunityModel", back_populates="campaigns")
