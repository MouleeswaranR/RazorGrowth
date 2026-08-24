"""Session model for managing merchant growth analysis sessions."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Session(Base):
    """Represents a growth analysis session for a merchant."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    session_name: Mapped[str] = mapped_column(String(200), nullable=False)
    session_description: Mapped[str | None] = mapped_column(Text)
    
    # Session metadata
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, archived, completed
    total_opportunities_found: Mapped[int] = mapped_column(Integer, default=0)
    total_campaigns_launched: Mapped[int] = mapped_column(Integer, default=0)
    total_gmv_impact: Mapped[float] = mapped_column(default=0.0)
    
    # Session context and state
    session_context: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)
    latest_opportunity_id: Mapped[str | None] = mapped_column(String(50))
    latest_campaign_id: Mapped[str | None] = mapped_column(String(50))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, merchant_id={self.merchant_id}, name={self.session_name}, status={self.status})>"
