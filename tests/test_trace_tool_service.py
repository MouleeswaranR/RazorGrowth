from app.services.trace_tool_service import trace_tool_service
from app.services.trace_logger_service import trace_logger_service


def test_trace_tool_service_routing():
    """Verifies that TraceToolService extracts targeted payload according to query intent."""
    session_id = "test_tool_session_123"

    # Seed mock trace
    trace_logger_service.log_trace_step(
        run_id="merch_test",
        session_id=session_id,
        step_name="3_campaign_launch_and_dispatch",
        step_data={
            "total_audience": 248,
            "treatment_group_size": 198,
            "control_group_size": 50,
            "target_segment": "VIP Dormant",
            "audience_reasoning": "Targeted 248 dormant VIPs with high lifetime value.",
            "offer": {
                "offer_code": "VIP15OFF",
                "discount_type": "percentage",
                "discount_value": 15.0,
                "description": "15% off orders above ₹1,999",
            },
            "offer_reasoning": "VIP re-engagement incentive.",
            "emails_dispatched": 198,
        },
    )

    trace_logger_service.log_trace_step(
        run_id="merch_test",
        session_id=session_id,
        step_name="4_experiment_ab_lift_measurement",
        step_data={
            "metrics": {
                "treatment_conversion_rate": 0.125,
                "control_conversion_rate": 0.040,
                "conversion_lift_percentage": 212.5,
                "absolute_difference_percentage": 8.5,
                "incremental_orders_count": 16,
                "incremental_revenue_inr": 45600.0,
                "status_note": "Treatment generated +16 incremental orders",
            },
        },
    )

    # Test audience routing
    audience_res = trace_tool_service.route_and_fetch_relevant_context("Why was this audience count selected?", session_id)
    assert audience_res["tool"] == "get_audience_breakdown"
    assert audience_res["data"]["total_audience"] == 248

    # Test experiment routing
    exp_res = trace_tool_service.route_and_fetch_relevant_context("What experiments were run and what is the GMV lift?", session_id)
    assert exp_res["tool"] == "get_experiment_lift_summary"
    assert exp_res["data"]["incremental_orders"] == 16
    assert "₹45,600.00" in exp_res["data"]["incremental_gmv_inr"]

    # Test offer routing
    offer_res = trace_tool_service.route_and_fetch_relevant_context("Why did you choose this coupon discount?", session_id)
    assert offer_res["tool"] == "get_campaign_offer_details"
    assert offer_res["data"]["offer_code"] == "VIP15OFF"


def test_trace_tool_service_session_isolation():
    """Verifies that an unseeded or new session_id does not leak previous session data."""
    unseeded_session_id = "completely_fresh_session_999"
    res = trace_tool_service.get_experiment_lift_summary(unseeded_session_id)
    assert res["treatment_conversions"] == 0
    assert res["incremental_orders"] == 0
    assert res["status_summary"] == "No experiment launched yet in this session."
