import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_full_autonomous_growth_api_loop():
    """Verifies the complete 7-step autonomous loop through the FastAPI HTTP endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Generate synthetic merchant data
        sim_res = await client.post("/api/v1/simulator/generate?merchant_name=StyleKart&customer_count=50&order_count=150")
        assert sim_res.status_code == 200
        sim_data = sim_res.json()["data"]
        merchant_id = sim_data["merchant_id"]
        assert merchant_id.startswith("merch_")

        # 2. Inspect local snapshot
        snap_res = await client.get("/api/v1/simulator/local-snapshot")
        assert snap_res.status_code == 200
        assert snap_res.json()["data"]["merchant_id"] == merchant_id

        # 3. Growth scan
        scan_res = await client.post(f"/api/v1/growth/scan/{merchant_id}")
        assert scan_res.status_code == 200
        scan_data = scan_res.json()
        assert scan_data["status"] == "success"
        assert scan_data["opportunities_found"] > 0
        opp_id = scan_data["opportunities"][0]["id"]

        # 4. Launch campaign (with permission gate bypass for headless automated testing)
        launch_res = await client.post(f"/api/v1/campaigns/launch/{opp_id}?bypass_permission_gate=true")
        assert launch_res.status_code == 200
        launch_data = launch_res.json()
        assert launch_data["status"] == "launched"
        campaign_id = launch_data["campaign_id"]
        assert launch_data["emails_dispatched"] >= 0

        # 5. Trigger a real test payment via webhook lifecycle (no simulation)
        target_customer_id = "cust_" + merchant_id[6:14]
        pay_res = await client.post(
            f"/api/v1/experiments/webhook-payment"
            f"?campaign_id={campaign_id}&customer_id={target_customer_id}&amount=2850"
        )
        assert pay_res.status_code == 200
        pay_data = pay_res.json()
        assert pay_data["status"] == "test_payment_captured_via_webhook"
        assert "metrics" in pay_data

        # 6. Read real measured results from PostgreSQL experiment_assignments
        results_res = await client.get(f"/api/v1/experiments/results/{campaign_id}")
        assert results_res.status_code == 200
        results_data = results_res.json()
        assert results_data["status"] == "measured"
        assert results_data["measured_via"] == "Razorpay Test Webhooks & PostgreSQL experiment_assignments"
        assert "treatment_conversion_rate" in results_data["metrics"]

        # 7. Test interactive AI chat
        chat_res = await client.post(
            "/api/v1/growth/chat",
            json={"merchant_id": merchant_id, "query": "Why did revenue drop this week?"},
        )
        assert chat_res.status_code == 200
        assert "reply" in chat_res.json()
