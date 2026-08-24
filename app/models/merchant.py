from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class MerchantModel(Base):
    """Represents a merchant entity storing business credentials and metadata."""

    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customers = relationship("CustomerModel", back_populates="merchant", lazy="selectin")
    products = relationship("ProductModel", back_populates="merchant", lazy="selectin")
    opportunities = relationship("OpportunityModel", back_populates="merchant", lazy="selectin")
