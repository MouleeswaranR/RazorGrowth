import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _launch_campaign(client: AsyncClient) -> dict:
    """Creates a campaign with representative treatment and control checkout sessions."""
    simulation = await client.post(
        "/api/v1/simulator/generate?merchant_name=IntegrityTest&customer_count=50&order_count=120"
    )
    merchant_id = simulation.json()["data"]["merchant_id"]
    scan = await client.post(f"/api/v1/growth/scan/{merchant_id}")
    opportunities = scan.json()["opportunities"]
    # Pick opportunity with largest audience to guarantee both treatment & control cohorts
    opp = max(opportunities, key=lambda x: x.get("audience_count", 0))
    launch = await client.post(
        f"/api/v1/campaigns/launch/{opp['id']}?bypass_permission_gate=true"
    )
    assert launch.status_code == 200
    return launch.json()



@pytest.mark.asyncio
async def test_records_treatment_and_control_conversions_by_order_id():
    """Measures both cohorts through their saved Razorpay order attribution."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        launch = await _launch_campaign(client)
        treatment = next(item for item in launch["checkout_sessions"] if item["variant"] == "treatment")
        control = next(item for item in launch["checkout_sessions"] if item["variant"] == "control")

        for checkout in (treatment, control):
            response = await client.post("/api/v1/experiments/webhook-payment", params={
                "campaign_id": launch["campaign_id"],
                "customer_id": checkout["customer_id"],
                "variant": checkout["variant"],
                "order_id": checkout["razorpay_order_id"],
                "amount": checkout["amount"],
            })
            assert response.status_code == 200

        results = await client.get(f"/api/v1/experiments/results/{launch['campaign_id']}")
        metrics = results.json()["metrics"]
        assert metrics["treatment_orders_count"] == 1
        assert metrics["control_orders_count"] == 1
        assert metrics["control_conversion_rate"] > 0


@pytest.mark.asyncio
async def test_replayed_payment_is_idempotent_and_variant_mismatch_is_rejected():
    """Prevents duplicate payment records and invalid cohort attribution."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        launch = await _launch_campaign(client)
        treatment = next(item for item in launch["checkout_sessions"] if item["variant"] == "treatment")
        params = {
            "campaign_id": launch["campaign_id"],
            "customer_id": treatment["customer_id"],
            "variant": "treatment",
            "order_id": treatment["razorpay_order_id"],
            "payment_id": "pay_idempotency_test",
            "amount": treatment["amount"],
        }
        first = await client.post("/api/v1/experiments/webhook-payment", params=params)
        replay = await client.post("/api/v1/experiments/webhook-payment", params=params)
        invalid = await client.post("/api/v1/experiments/webhook-payment", params={
            **params, "payment_id": "pay_invalid_variant", "variant": "control"
        })

        assert first.status_code == 200
        assert replay.status_code == 200
        assert invalid.status_code == 422
        results = await client.get(f"/api/v1/experiments/results/{launch['campaign_id']}")
        assert results.json()["metrics"]["treatment_orders_count"] == 1
