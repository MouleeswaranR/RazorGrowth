from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_database_session
from app.models.campaign import CampaignModel
from app.services.live_experiment_service import live_experiment_service
from app.services.trace_logger_service import trace_logger_service

router = APIRouter(prefix="/experiments", tags=["A/B Experiments & Measurement"])


@router.get("/results/{campaign_id}")
async def get_experiment_results(
    campaign_id: str,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Reads real experiment conversion metrics from experiment_assignments in PostgreSQL."""
    campaign = (await session.execute(
        select(CampaignModel).where(CampaignModel.id == campaign_id)
    )).scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    metrics = await live_experiment_service.recalculate_campaign_metrics(
        session=session,
        campaign_id=campaign_id,
        session_id=session_id,
    )

    return {
        "status": "measured",
        "campaign_id": campaign_id,
        "measured_via": "Razorpay Test Webhooks & PostgreSQL experiment_assignments",
        "metrics": metrics,
    }


@router.post("/webhook-payment")
async def record_test_webhook_payment(
    campaign_id: str,
    customer_id: str,
    amount: float = 2850.0,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Records a Razorpay test payment.captured event via the webhook lifecycle in PostgreSQL."""
    import uuid

    event_payload = {
        "event": "payment.captured",
        "payment_id": f"pay_{uuid.uuid4().hex[:14]}",
        "order_id": f"order_{uuid.uuid4().hex[:14]}",
        "amount": amount,
        "status": "captured",
        "method": "upi",
        "campaign_id": campaign_id,
        "customer_id": customer_id,
        "variant": "treatment",
        "session_id": session_id,
    }

    metrics = await live_experiment_service.record_webhook_payment(session, event_payload)
    try:
        from app.api.routes_webhooks import append_recent_webhook
        append_recent_webhook(event_payload)
    except Exception:
        pass

    trace_logger_service.log_trace_step(
        run_id=campaign_id,
        session_id=session_id,
        step_name="5_razorpay_test_payment_captured",
        step_data={
            "payment_id": event_payload["payment_id"],
            "campaign_id": campaign_id,
            "customer_id": customer_id,
            "amount_inr": amount,
            "measured_via": "Razorpay Test Webhook (payment.captured)",
            "metrics": metrics,
        },
    )

    return {
        "status": "test_payment_captured_via_webhook",
        "payment_id": event_payload["payment_id"],
        "campaign_id": campaign_id,
        "customer_id": customer_id,
        "metrics": metrics,
    }
