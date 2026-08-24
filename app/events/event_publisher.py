import uuid
from app.events.event_types import DomainEvent, EventType


class InMemoryEventPublisher:
    """Publishes domain events to subscribed in-memory event listeners."""

    def __init__(self) -> None:
        """Initializes empty list of registered listeners."""
        self._listeners: list = []

    def register_listener(self, listener_callable) -> None:
        """Registers a callable subscriber to receive published events."""
        self._listeners.append(listener_callable)

    async def publish(self, event_type: EventType, payload: dict) -> DomainEvent:
        """Constructs and broadcasts an event to all registered listeners."""
        event = DomainEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            payload=payload,
        )
        for listener in self._listeners:
            await listener(event)
        return event


event_publisher = InMemoryEventPublisher()
