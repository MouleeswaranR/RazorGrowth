import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.integrations.razorpay_client import razorpay_client
from app.integrations.razorpay_webhook_handler import razorpay_webhook_handler


@pytest.mark.anyio
async def test_razorpay_client_create_order_with_notes():
    """Validates that create_order includes custom metadata notes."""
    notes = {
        "campaign_id": "cmp_test_123",
        "customer_id": "cust_test_456",
        "variant": "treatment",
    }
    order = razorpay_client.create_order(
        amount_in_paise=285000,
        receipt="rcpt_test",
        notes=notes,
    )
    assert order is not None
    assert "id" in order
    assert order.get("amount") == 285000
    assert order.get("notes", {}).get("campaign_id") == "cmp_test_123"


def test_razorpay_webhook_handler_extract_notes():
    """Validates that webhook extractor pulls entity notes and payment identifiers."""
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_999",
                    "order_id": "order_test_888",
                    "amount": 285000,
                    "status": "captured",
                    "method": "upi",
                    "notes": {
                        "campaign_id": "cmp_unit_test",
                        "customer_id": "cust_unit_test",
                        "variant": "treatment",
                    },
                }
            }
        },
    }
    extracted = razorpay_webhook_handler.extract_event_payload(payload)
    assert extracted["event"] == "payment.captured"
    assert extracted["payment_id"] == "pay_test_999"
    assert extracted["amount"] == 2850.0
    assert extracted["campaign_id"] == "cmp_unit_test"
    assert extracted["customer_id"] == "cust_unit_test"


@pytest.mark.anyio
async def test_webhook_simulate_endpoint():
    """Validates that simulated test webhook endpoint records payment and recalculates metrics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/webhooks/simulate-test-event",
            params={
                "campaign_id": "cmp_mock_123",
                "customer_id": "cust_mock_456",
                "amount": 2850.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "simulated_webhook_processed"
        assert data["event"]["payment_id"].startswith("pay_")


@pytest.mark.anyio
async def test_recalculate_campaign_metrics_returns_sentinel_on_empty_assignments():
    """Verifies that recalculate_campaign_metrics returns explicit sentinel state on empty assignments."""
    from app.database.session import get_database_session
    from app.models.merchant import MerchantModel
    from app.models.opportunity import OpportunityModel
    from app.models.campaign import CampaignModel
    from app.services.live_experiment_service import live_experiment_service

    async for session in get_database_session():
        merchant = MerchantModel(
            id="merch_empty_sentinel_test",
            name="Sentinel Merchant",
            category="Apparel",
        )
        session.add(merchant)
        await session.flush()

        opportunity = OpportunityModel(
            id="opp_empty_sentinel_test",
            merchant_id=merchant.id,
            opportunity_type="customer_churn_prevention",
            title="Dormant VIP Recovery",
            description="Re-engage dormant VIPs",
            target_audience_count=50,
            estimated_gmv_impact=15000.0,
            confidence_score=0.88,
            status="discovered",
        )
        session.add(opportunity)
        await session.flush()

        # Create temporary campaign with no assignments
        campaign = CampaignModel(
            id="cmp_empty_sentinel_test",
            opportunity_id=opportunity.id,
            name="Empty Sentinel Test Campaign",
            channel="email",
            offer_details="15% Off",
            message_copy="Code: VIP15",
            status="active",
            target_customer_count=50,
        )
        session.add(campaign)
        await session.commit()

        metrics = await live_experiment_service.recalculate_campaign_metrics(
            session=session,
            campaign_id="cmp_empty_sentinel_test",
        )

        assert metrics["status_note"] == "no_conversions_recorded_yet"
        assert metrics["treatment_conversion_rate"] == 0.0
        assert metrics["control_conversion_rate"] == 0.0
        assert metrics["incremental_orders_count"] == 0
        assert metrics["incremental_revenue_inr"] == 0.0

        # Cleanup
        await session.delete(campaign)
        await session.delete(opportunity)
        await session.delete(merchant)
        await session.commit()
        break

