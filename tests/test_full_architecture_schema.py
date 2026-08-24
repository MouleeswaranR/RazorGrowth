import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_full_architecture_webhook_and_assignment_pipeline():
    """Validates complete PostgreSQL flow with webhook_events and experiment_assignments via HTTP."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Generate merchant data to seed the DB cleanly
        sim_res = await client.post(
            "/api/v1/simulator/generate?merchant_name=ArchTest&customer_count=50&order_count=150"
        )
        assert sim_res.status_code == 200
        merchant_id = sim_res.json()["data"]["merchant_id"]

        # 2. Scan for opportunities
        scan_res = await client.post(f"/api/v1/growth/scan/{merchant_id}")
        assert scan_res.status_code == 200
        opp_id = scan_res.json()["opportunities"][0]["id"]

        # 3. Launch campaign — this creates real Razorpay Test Orders + experiment_assignments
        launch_res = await client.post(
            f"/api/v1/campaigns/launch/{opp_id}?bypass_permission_gate=true"
        )
        assert launch_res.status_code == 200
        launch_data = launch_res.json()
        assert launch_data["status"] == "launched"
        campaign_id = launch_data["campaign_id"]

        # 4. Simulate a real webhook payment capture — writes to webhook_events + experiment_assignments
        checkout_sessions = launch_data.get("checkout_sessions", [])
        customer_id = (
            checkout_sessions[0]["customer_id"]
            if checkout_sessions
            else f"cust_{merchant_id[6:14]}"
        )

        webhook_res = await client.post(
            f"/api/v1/experiments/webhook-payment"
            f"?campaign_id={campaign_id}&customer_id={customer_id}&amount=2850"
        )
        assert webhook_res.status_code == 200
        webhook_data = webhook_res.json()
        assert webhook_data["status"] == "test_payment_captured_via_webhook"
        assert "metrics" in webhook_data

        # 5. Read real recalculated metrics from PostgreSQL experiment_assignments
        results_res = await client.get(f"/api/v1/experiments/results/{campaign_id}")
        assert results_res.status_code == 200
        results = results_res.json()
        assert results["status"] == "measured"
        assert results["measured_via"] == "Razorpay Test Webhooks & PostgreSQL experiment_assignments"

        metrics = results["metrics"]
        assert "treatment_conversion_rate" in metrics
        assert "control_conversion_rate" in metrics
        assert metrics["treatment_conversion_rate"] > 0.0

        # 6. Verify recent webhooks were captured
        webhooks_res = await client.get("/api/v1/webhooks/recent")
        assert webhooks_res.status_code == 200
