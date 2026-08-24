"""Conversation and message models for storing chat history."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Conversation(Base):
    """Represents a conversation thread within a session."""
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(50), ForeignKey("sessions.id"), nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    
    # Conversation metadata
    conversation_title: Mapped[str] = mapped_column(String(200), nullable=False)
    conversation_type: Mapped[str] = mapped_column(String(50), default="chat", nullable=False)  # chat, analysis, campaign
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    
    # Vectorization status
    is_vectorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vector_id: Mapped[str | None] = mapped_column(String(100))  # ChromaDB collection ID
    
    # Cross-reference tracking
    referenced_session_ids: Mapped[list] = mapped_column(JSON, default=[], nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, session_id={self.session_id}, title={self.conversation_title})>"


class ConversationMessage(Base):
    """Represents a single message in a conversation."""
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(50), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Optional AI metadata
    reasoning_trace: Mapped[str | None] = mapped_column(Text)
    provider_used: Mapped[str | None] = mapped_column(String(50))
    suggested_action: Mapped[str | None] = mapped_column(Text)
    
    # Message metadata
    message_metadata: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
