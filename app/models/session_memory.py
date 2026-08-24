from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class SessionMemoryModel(Base):
    """Stores episodic outcome memories and growth reasoning for vector search retrieval."""

    __tablename__ = "session_memories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id"), index=True)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
