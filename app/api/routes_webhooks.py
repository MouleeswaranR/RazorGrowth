from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_database_session
from app.integrations.razorpay_webhook_handler import razorpay_webhook_handler
from app.events.event_publisher import event_publisher
from app.events.event_types import EventType
from app.services.live_experiment_service import live_experiment_service

router = APIRouter(prefix="/webhooks", tags=["Razorpay Webhooks"])

_recent_webhooks: list = []


@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Receives, verifies, persists, and recalculates real-time Razorpay payment webhook events."""
    raw_body = await request.body()
    is_valid = razorpay_webhook_handler.verify_signature(raw_body, x_razorpay_signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    parsed_event = razorpay_webhook_handler.extract_event_payload(payload)

    _recent_webhooks.append(parsed_event)
    if len(_recent_webhooks) > 50:
        _recent_webhooks.pop(0)

    # Persist and recalculate live metrics in PostgreSQL
    result = await live_experiment_service.record_webhook_payment(session, parsed_event)

    await event_publisher.publish(
        event_type=EventType.PAYMENT_CAPTURED,
        payload=parsed_event,
    )
    return {
        "status": "received",
        "event": parsed_event.get("event"),
        "metrics": result,
    }


@router.get("/recent")
async def get_recent_webhooks() -> dict:
    """Returns the buffer of recently received Razorpay webhooks."""
    return {"total": len(_recent_webhooks), "events": _recent_webhooks[-10:]}


@router.post("/simulate-test-event")
async def simulate_test_webhook_event(
    campaign_id: str,
    customer_id: str,
    amount: float = 2850.0,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Simulates a real-time Razorpay payment.captured webhook for testing ngrok and live flow."""
    import uuid
    mock_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:14]}",
                    "order_id": f"order_{uuid.uuid4().hex[:14]}",
                    "amount": int(amount * 100),
                    "status": "captured",
                    "method": "upi",
                    "notes": {
                        "campaign_id": campaign_id,
                        "customer_id": customer_id,
                        "variant": "treatment",
                        "session_id": session_id or "",
                    },
                }
            }
        },
    }
    parsed = razorpay_webhook_handler.extract_event_payload(mock_payload)
    _recent_webhooks.append(parsed)
    metrics = await live_experiment_service.record_webhook_payment(session, parsed)
    return {
        "status": "simulated_webhook_processed",
        "event": parsed,
        "metrics": metrics,
    }

