"""Session management service for handling growth analysis sessions."""
import logging
from datetime import datetime
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session

logger = logging.getLogger(__name__)


class SessionManagementService:
    """Manages merchant growth analysis sessions."""

    @staticmethod
    async def create_session(
        session: AsyncSession,
        merchant_id: str,
        session_name: str,
        session_description: str | None = None,
        session_context: dict | None = None,
    ) -> Session:
        """Create a new growth analysis session."""
        import uuid
        
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        new_session = Session(
            id=session_id,
            merchant_id=merchant_id,
            session_name=session_name,
            session_description=session_description or "",
            session_context=session_context or {},
            status="active",
            total_opportunities_found=0,
            total_campaigns_launched=0,
            total_gmv_impact=0.0,
        )
        
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)
        
        logger.info(f"Created session {session_id} for merchant {merchant_id}")
        return new_session

    @staticmethod
    async def get_session(session: AsyncSession, session_id: str) -> Session | None:
        """Retrieve a session by ID."""
        result = await session.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_merchant_sessions(
        session: AsyncSession,
        merchant_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        """List all sessions for a merchant."""
        query = select(Session).where(Session.merchant_id == merchant_id)
        
        if status:
            query = query.where(Session.status == status)
        
        query = query.order_by(desc(Session.last_activity_at)).limit(limit).offset(offset)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_session(
        session: AsyncSession,
        session_id: str,
        **update_fields,
    ) -> Session | None:
        """Update session fields."""
        update_fields["updated_at"] = datetime.utcnow()
        update_fields["last_activity_at"] = datetime.utcnow()
        
        await session.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(**update_fields)
        )
        await session.commit()
        
        return await SessionManagementService.get_session(session, session_id)

    @staticmethod
    async def archive_session(session: AsyncSession, session_id: str) -> None:
        """Archive a session."""
        await SessionManagementService.update_session(
            session, session_id, status="archived"
        )
        logger.info(f"Archived session {session_id}")

    @staticmethod
    async def delete_session(session: AsyncSession, session_id: str) -> None:
        """Delete a session and all its conversations."""
        db_session = await SessionManagementService.get_session(session, session_id)
        if db_session:
            await session.delete(db_session)
            await session.commit()
            logger.info(f"Deleted session {session_id}")

session_management_service = SessionManagementService()
