from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class EventType(str, Enum):
    """Enumeration of standard domain event types."""
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    ORDER_CREATED = "order.created"
    CAMPAIGN_TRIGGERED = "campaign.triggered"
    OPPORTUNITY_DETECTED = "opportunity.detected"


class DomainEvent(BaseModel):
    """Schema representing an event object broadcast within the system."""
    event_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict
