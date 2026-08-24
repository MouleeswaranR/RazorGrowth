import logging
from app.events.event_types import DomainEvent, EventType
from app.events.event_publisher import event_publisher

logger = logging.getLogger(__name__)


async def handle_incoming_payment_event(event: DomainEvent) -> None:
    """Processes payment success or failure events to log domain activity."""
    if event.event_type == EventType.PAYMENT_CAPTURED:
        order_id = event.payload.get("order_id")
        amount = event.payload.get("amount")
        logger.info(f"[DomainEvent] Payment captured processed for order {order_id} (INR {amount})")


def register_default_event_consumers() -> None:
    """Registers core domain event handler functions with the global event publisher."""
    event_publisher.register_listener(handle_incoming_payment_event)
