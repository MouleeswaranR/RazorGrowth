"""API endpoints for session and conversation management."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.database.session import AsyncSessionLocal
from app.services.session_management_service import session_management_service
from app.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)
router = APIRouter()


# === Pydantic Schemas ===

class SessionCreate(BaseModel):
    merchant_id: str = Field(..., description="Merchant ID")
    session_name: str = Field(..., description="Session name")
    session_description: str | None = Field(None, description="Session description")
    session_context: dict = Field(default_factory=dict, description="Initial session context")


class SessionUpdate(BaseModel):
    session_name: str | None = None
    session_description: str | None = None
    session_context: dict | None = None
    status: str | None = None


class ConversationCreate(BaseModel):
    session_id: str = Field(..., description="Session ID")
    merchant_id: str = Field(..., description="Merchant ID")
    conversation_title: str = Field(..., description="Conversation title")
    conversation_type: str = Field(default="chat", description="Conversation type")


class MessageCreate(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    reasoning_trace: str | None = Field(None, description="AI reasoning trace")
    provider_used: str | None = Field(None, description="LLM provider used")
    suggested_action: str | None = Field(None, description="Suggested follow-up action")
    message_metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SessionReferenceAdd(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID")
    referenced_session_id: str = Field(..., description="Referenced session ID")


class ConversationSearch(BaseModel):
    query: str = Field(..., description="Search query")
    merchant_id: str | None = Field(None, description="Filter by merchant")
    session_id: str | None = Field(None, description="Filter by session")
    limit: int = Field(default=5, description="Max results")


# === Session Endpoints ===

@router.post("/sessions/create")
async def create_session(data: SessionCreate):
    """Create a new growth analysis session."""
    async with AsyncSessionLocal() as db_session:
        try:
            session = await session_management_service.create_session(
                db_session,
                merchant_id=data.merchant_id,
                session_name=data.session_name,
                session_description=data.session_description,
                session_context=data.session_context,
            )
            
            return {
                "success": True,
                "session_id": session.id,
                "session_name": session.session_name,
                "created_at": session.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    async with AsyncSessionLocal() as db_session:
        session = await session_management_service.get_session(db_session, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "id": session.id,
            "merchant_id": session.merchant_id,
            "session_name": session.session_name,
            "session_description": session.session_description,
            "status": session.status,
            "total_opportunities_found": session.total_opportunities_found,
            "total_campaigns_launched": session.total_campaigns_launched,
            "total_gmv_impact": session.total_gmv_impact,
            "session_context": session.session_context,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
        }


@router.get("/sessions/merchant/{merchant_id}")
async def list_merchant_sessions(
    merchant_id: str,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all sessions for a merchant."""
    async with AsyncSessionLocal() as db_session:
        sessions = await session_management_service.list_merchant_sessions(
            db_session, merchant_id, status=status, limit=limit, offset=offset
        )
        
        return {
            "sessions": [
                {
                    "id": s.id,
                    "session_name": s.session_name,
                    "status": s.status,
                    "total_opportunities_found": s.total_opportunities_found,
                    "total_campaigns_launched": s.total_campaigns_launched,
                    "total_gmv_impact": s.total_gmv_impact,
                    "created_at": s.created_at.isoformat(),
                    "last_activity_at": s.last_activity_at.isoformat(),
                }
                for s in sessions
            ],
            "total": len(sessions),
        }


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, data: SessionUpdate):
    """Update session details."""
    async with AsyncSessionLocal() as db_session:
        update_fields = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        session = await session_management_service.update_session(
            db_session, session_id, **update_fields
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "session_id": session.id}


@router.post("/sessions/{session_id}/archive")
async def archive_session(session_id: str):
    """Archive a session."""
    async with AsyncSessionLocal() as db_session:
        await session_management_service.archive_session(db_session, session_id)
        return {"success": True, "session_id": session_id, "status": "archived"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its conversations."""
    async with AsyncSessionLocal() as db_session:
        await session_management_service.delete_session(db_session, session_id)
        return {"success": True, "message": "Session deleted"}


# === Conversation Endpoints ===

@router.post("/conversations/create")
async def create_conversation(data: ConversationCreate):
    """Create a new conversation thread."""
    async with AsyncSessionLocal() as db_session:
        try:
            conversation = await conversation_service.create_conversation(
                db_session,
                session_id=data.session_id,
                merchant_id=data.merchant_id,
                conversation_title=data.conversation_title,
                conversation_type=data.conversation_type,
            )
            
            return {
                "success": True,
                "conversation_id": conversation.id,
                "session_id": conversation.session_id,
                "created_at": conversation.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/message")
async def add_message(data: MessageCreate):
    """Add a message to a conversation."""
    async with AsyncSessionLocal() as db_session:
        try:
            message = await conversation_service.add_message(
                db_session,
                conversation_id=data.conversation_id,
                role=data.role,
                content=data.content,
                reasoning_trace=data.reasoning_trace,
                provider_used=data.provider_used,
                suggested_action=data.suggested_action,
                message_metadata=data.message_metadata,
            )
            
            return {
                "success": True,
                "message_id": message.id,
                "conversation_id": message.conversation_id,
                "created_at": message.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int | None = None):
    """Get all messages in a conversation."""
    async with AsyncSessionLocal() as db_session:
        messages = await conversation_service.get_conversation_messages(
            db_session, conversation_id, limit=limit
        )
        
        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "reasoning_trace": m.reasoning_trace,
                    "provider_used": m.provider_used,
                    "suggested_action": m.suggested_action,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
            "total": len(messages),
        }


@router.get("/conversations/session/{session_id}")
async def list_session_conversations(session_id: str, limit: int = 50):
    """List all conversations in a session."""
    async with AsyncSessionLocal() as db_session:
        conversations = await conversation_service.list_session_conversations(
            db_session, session_id, limit=limit
        )
        
        return {
            "session_id": session_id,
            "conversations": [
                {
                    "id": c.id,
                    "conversation_title": c.conversation_title,
                    "conversation_type": c.conversation_type,
                    "total_messages": c.total_messages,
                    "is_vectorized": c.is_vectorized,
                    "referenced_session_ids": c.referenced_session_ids,
                    "created_at": c.created_at.isoformat(),
                    "last_message_at": c.last_message_at.isoformat(),
                }
                for c in conversations
            ],
            "total": len(conversations),
        }


@router.post("/conversations/{conversation_id}/vectorize")
async def vectorize_conversation(conversation_id: str):
    """Vectorize a conversation for semantic search."""
    async with AsyncSessionLocal() as db_session:
        success = await conversation_service.vectorize_conversation(
            db_session, conversation_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to vectorize conversation")
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversation vectorized successfully",
        }


@router.post("/conversations/add-reference")
async def add_session_reference(data: SessionReferenceAdd):
    """Add a cross-reference to another session."""
    async with AsyncSessionLocal() as db_session:
        await conversation_service.add_session_reference(
            db_session,
            conversation_id=data.conversation_id,
            referenced_session_id=data.referenced_session_id,
        )
        
        return {
            "success": True,
            "conversation_id": data.conversation_id,
            "referenced_session_id": data.referenced_session_id,
        }


@router.post("/conversations/search")
async def search_conversations(data: ConversationSearch):
    """Search conversations using vector similarity."""
    try:
        results = await conversation_service.search_conversations(
            query=data.query,
            merchant_id=data.merchant_id,
            session_id=data.session_id,
            limit=data.limit,
        )
        
        return {
            "query": data.query,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        logger.error(f"Failed to search conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
