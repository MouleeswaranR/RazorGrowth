"""Conversation service for storing and vectorizing chat conversations."""
import logging
import json
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, ConversationMessage
from app.services.vector_memory_service import VectorMemoryService

logger = logging.getLogger(__name__)


class ConversationService:
    """Manages conversations and their vectorization."""

    def __init__(self):
        self.vector_service = VectorMemoryService()

    async def create_conversation(
        self,
        session: AsyncSession,
        session_id: str,
        merchant_id: str,
        conversation_title: str,
        conversation_type: str = "chat",
    ) -> Conversation:
        """Create a new conversation thread."""
        import uuid
        
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        new_conversation = Conversation(
            id=conversation_id,
            session_id=session_id,
            merchant_id=merchant_id,
            conversation_title=conversation_title,
            conversation_type=conversation_type,
            total_messages=0,
            is_vectorized=False,
            referenced_session_ids=[],
        )
        
        session.add(new_conversation)
        await session.commit()
        await session.refresh(new_conversation)
        
        logger.info(f"Created conversation {conversation_id} in session {session_id}")
        return new_conversation

    async def add_message(
        self,
        session: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        reasoning_trace: str | None = None,
        provider_used: str | None = None,
        suggested_action: str | None = None,
        message_metadata: dict | None = None,
    ) -> ConversationMessage:
        """Add a message to a conversation."""
        import uuid
        
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        new_message = ConversationMessage(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            reasoning_trace=reasoning_trace,
            provider_used=provider_used,
            suggested_action=suggested_action,
            message_metadata=message_metadata or {},
        )
        
        session.add(new_message)
        
        # Update conversation metadata
        conversation = await self.get_conversation(session, conversation_id)
        if conversation:
            conversation.total_messages += 1
            conversation.last_message_at = datetime.utcnow()
            conversation.is_vectorized = False  # Mark as needs re-vectorization
        
        await session.commit()
        await session.refresh(new_message)
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        return new_message

    async def get_conversation(
        self,
        session: AsyncSession,
        conversation_id: str,
    ) -> Conversation | None:
        """Retrieve a conversation by ID."""
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_conversation_messages(
        self,
        session: AsyncSession,
        conversation_id: str,
        limit: int | None = None,
    ) -> list[ConversationMessage]:
        """Get all messages in a conversation."""
        query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at)
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def list_session_conversations(
        self,
        session: AsyncSession,
        session_id: str,
        limit: int = 50,
    ) -> list[Conversation]:
        """List all conversations in a session."""
        result = await session.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(desc(Conversation.last_message_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def vectorize_conversation(
        self,
        session: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """Vectorize an entire conversation for semantic search."""
        try:
            conversation = await self.get_conversation(session, conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return False
            
            messages = await self.get_conversation_messages(session, conversation_id)
            if not messages:
                logger.warning(f"No messages in conversation {conversation_id}")
                return False
            
            # Build conversation summary
            conversation_text = f"Conversation: {conversation.conversation_title}\n\n"
            for msg in messages:
                conversation_text += f"{msg.role}: {msg.content}\n"
                if msg.reasoning_trace:
                    conversation_text += f"[Reasoning: {msg.reasoning_trace}]\n"
                conversation_text += "\n"
            
            # Store in vector memory
            metadata = {
                "type": "conversation",
                "conversation_id": conversation_id,
                "session_id": conversation.session_id,
                "merchant_id": conversation.merchant_id,
                "conversation_type": conversation.conversation_type,
                "total_messages": conversation.total_messages,
                "created_at": conversation.created_at.isoformat(),
            }
            
            vector_id = f"mem_conv_{conversation_id}"
            self.vector_service.store_memory(
                memory_id=vector_id,
                merchant_id=conversation.merchant_id,
                memory_type="conversation",
                summary_text=conversation_text,
                metadata=metadata,
            )
            
            # Update conversation
            conversation.is_vectorized = True
            conversation.vector_id = vector_id
            await session.commit()
            
            logger.info(f"Vectorized conversation {conversation_id} with vector_id {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to vectorize conversation {conversation_id}: {e}")
            return False

    async def add_session_reference(
        self,
        session: AsyncSession,
        conversation_id: str,
        referenced_session_id: str,
    ) -> None:
        """Add a cross-reference to another session."""
        conversation = await self.get_conversation(session, conversation_id)
        if conversation:
            if referenced_session_id not in conversation.referenced_session_ids:
                conversation.referenced_session_ids.append(referenced_session_id)
                await session.commit()
                logger.info(f"Added session reference {referenced_session_id} to conversation {conversation_id}")

    async def search_conversations(
        self,
        query: str,
        merchant_id: str | None = None,
        session_id: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Search conversations using vector similarity."""
        results = self.vector_service.find_similar_memories(
            merchant_id=merchant_id or "",
            query_text=query,
            top_k=limit,
        )
        return results

    async def get_or_create_conversation(
        self,
        session: AsyncSession,
        session_id: str,
        merchant_id: str,
        conversation_title: str | None = None,
    ) -> Conversation:
        """Get the most recent conversation or create a new one."""
        # Try to get most recent conversation in this session
        result = await session.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(desc(Conversation.last_message_at))
            .limit(1)
        )
        
        existing_conversation = result.scalar_one_or_none()
        if existing_conversation:
            return existing_conversation
        
        # Create new conversation
        return await self.create_conversation(
            session,
            session_id=session_id,
            merchant_id=merchant_id,
            conversation_title=conversation_title or "New Conversation",
            conversation_type="chat",
        )


conversation_service = ConversationService()
