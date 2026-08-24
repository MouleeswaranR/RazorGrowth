from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class OpportunityModel(Base):
    """Represents an AI-discovered growth opportunity with impact estimates."""

    __tablename__ = "growth_opportunities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=False)
    target_audience_count: Mapped[int] = mapped_column(nullable=False, default=0)
    estimated_gmv_impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="detected")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    merchant = relationship("MerchantModel", back_populates="opportunities")
    campaigns = relationship("CampaignModel", back_populates="opportunity", lazy="selectin")
