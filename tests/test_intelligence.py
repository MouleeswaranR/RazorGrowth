from datetime import datetime, timezone, timedelta
from app.models.customer import CustomerModel
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.intelligence.distribution_thresholds import compute_merchant_distribution_thresholds
from app.intelligence.customer_segmentation import classify_customer_segment, compute_rfm_composite_score
from app.intelligence.churn_predictor import calculate_churn_risk_score, calculate_churn_risk_with_orders
from app.intelligence.clv_estimator import estimate_customer_lifetime_value
from app.intelligence.product_recommender import build_category_copurchase_matrix, find_cross_sell_candidates
from app.intelligence.payment_method_analyzer import analyze_payment_method_performance, find_underperforming_payment_methods
from app.intelligence.opportunity_detector import (
    detect_dormant_vip_opportunity,
    detect_churn_intervention_opportunity,
    detect_aov_basket_builder_opportunity,
)


def test_segmentation_edge_cases():
    """Tests segmentation for zero orders, new users, and dormant VIPs."""
    now = datetime.now(timezone.utc)

    # Zero orders customer
    c_zero = CustomerModel(id="c0", merchant_id="m1", name="Zero", email="z@e.com", total_orders_count=0, total_spend_amount=0.0)
    assert classify_customer_segment(c_zero) == "Standard"

    # VIP Active customer
    c_vip_active = CustomerModel(
        id="c1", merchant_id="m1", name="VIP Active", email="v1@e.com",
        total_orders_count=8, total_spend_amount=15000.0, last_purchase_timestamp=now - timedelta(days=5),
    )
    assert classify_customer_segment(c_vip_active) == "VIP Active"

    # VIP Dormant customer
    c_vip_dormant = CustomerModel(
        id="c2", merchant_id="m1", name="VIP Dormant", email="v2@e.com",
        total_orders_count=6, total_spend_amount=9000.0, last_purchase_timestamp=now - timedelta(days=45),
    )
    assert classify_customer_segment(c_vip_dormant) == "VIP Dormant"

    # RFM score calculation
    rfm = compute_rfm_composite_score(c_vip_active)
    assert 0.0 <= rfm <= 1.0


def test_distribution_aware_adaptation():
    """Tests that quantile thresholds correctly adapt between low-AOV and high-AOV stores."""
    now = datetime.now(timezone.utc)

    # Low-AOV merchant (e.g. ₹150 average item store)
    low_aov_custs = [
        CustomerModel(
            id=f"low_{i}", merchant_id="m_low", name=f"Low {i}", email=f"l{i}@e.com",
            total_orders_count=i + 1, total_spend_amount=float((i + 1) * 150),
            last_purchase_timestamp=now - timedelta(days=i * 5),
        )
        for i in range(20)
    ]
    low_thresh = compute_merchant_distribution_thresholds(low_aov_custs)
    assert low_thresh.vip_spend_p90 < 3500.0  # Adapts down to low store spend

    # High-AOV luxury merchant (e.g. ₹20,000 average item store)
    high_aov_custs = [
        CustomerModel(
            id=f"high_{i}", merchant_id="m_high", name=f"High {i}", email=f"h{i}@e.com",
            total_orders_count=i + 1, total_spend_amount=float((i + 1) * 20000),
            last_purchase_timestamp=now - timedelta(days=i * 5),
        )
        for i in range(20)
    ]
    high_thresh = compute_merchant_distribution_thresholds(high_aov_custs)
    assert high_thresh.vip_spend_p90 > 250000.0  # Adapts up to luxury store spend

    # Both classify their top 10% customers appropriately relative to their own distribution
    top_low = low_aov_custs[-1]
    top_high = high_aov_custs[-1]
    assert classify_customer_segment(top_low, low_thresh) in ("VIP Active", "VIP Dormant")
    assert classify_customer_segment(top_high, high_thresh) in ("VIP Active", "VIP Dormant")


def test_churn_predictor_edge_cases():
    """Tests churn risk scoring with missing timestamps and continuous decay."""
    now = datetime.now(timezone.utc)

    # No timestamp -> highest risk (0.90)
    c_none = CustomerModel(id="c0", merchant_id="m1", name="None", email="n@e.com", last_purchase_timestamp=None)
    assert calculate_churn_risk_score(c_none) == 0.90

    # Recent customer -> low risk (< 0.10)
    c_recent = CustomerModel(id="c1", merchant_id="m1", name="Recent", email="r@e.com", last_purchase_timestamp=now - timedelta(days=2))
    assert calculate_churn_risk_score(c_recent) < 0.10

    # With empty orders list
    risk = calculate_churn_risk_with_orders(c_recent, [])
    assert 0.0 <= risk <= 1.0


def test_clv_estimator_edge_cases():
    """Tests continuous CLV estimation with zero orders and high churn discount."""
    # Zero orders
    c_zero = CustomerModel(id="c0", merchant_id="m1", name="Zero", email="z@e.com", total_orders_count=0, total_spend_amount=0.0)
    assert estimate_customer_lifetime_value(c_zero) == 1500.0

    # High churn customer should get discounted CLV
    c_churn = CustomerModel(
        id="c1", merchant_id="m1", name="Churn", email="c@e.com",
        total_orders_count=5, total_spend_amount=10000.0, churn_risk_score=0.90,
    )
    clv = estimate_customer_lifetime_value(c_churn)
    assert clv >= 10000.0


def test_copurchase_matrix_and_cross_sell():
    """Tests co-purchase matrix building and candidate extraction."""
    product_cat_map = {"p1": "Footwear", "p2": "Accessories", "p3": "Apparel"}
    orders = [
        OrderModel(id="o1", merchant_id="m1", customer_id="c1", product_id="p1", amount=2999.0),
        OrderModel(id="o2", merchant_id="m1", customer_id="c1", product_id="p2", amount=499.0),
        OrderModel(id="o3", merchant_id="m1", customer_id="c2", product_id="p1", amount=2999.0),
    ]

    matrix = build_category_copurchase_matrix(orders, product_cat_map)
    assert "Footwear" in matrix

    candidates = find_cross_sell_candidates(orders, product_cat_map, "Footwear", "Accessories")
    assert "c2" in candidates
    assert "c1" not in candidates


def test_payment_method_analyzer_edge_cases():
    """Tests payment analysis with zero payments and varying failure rates."""
    # Empty payments
    assert analyze_payment_method_performance([]) == {}

    # Sample payments
    payments = [
        PaymentModel(id="p1", order_id="o1", payment_method="upi", amount=1000.0, status="captured"),
        PaymentModel(id="p2", order_id="o2", payment_method="card", amount=2000.0, status="failed"),
    ]
    stats = analyze_payment_method_performance(payments)
    assert "upi" in stats
    assert stats["upi"]["success_rate"] == 1.0
    assert stats["card"]["success_rate"] == 0.0


def test_opportunity_detector_edge_cases():
    """Tests opportunity detection when 0 opportunities exist vs when present."""
    # Zero dormant VIPs
    assert detect_dormant_vip_opportunity("m1", []) is None

    # Multiple dormant VIPs
    dormant_vips = [
        CustomerModel(id=f"c_{i}", merchant_id="m1", name=f"VIP {i}", email=f"v{i}@e.com",
                      customer_segment="VIP Dormant", total_spend_amount=8000.0, total_orders_count=4)
        for i in range(5)
    ]
    opp = detect_dormant_vip_opportunity("m1", dormant_vips)
    assert opp is not None
    assert opp.target_audience_count == 5
    assert opp.estimated_gmv_impact > 0

    # Churn intervention opportunity
    at_risk_custs = [
        CustomerModel(id=f"ar_{i}", merchant_id="m1", name=f"Risk {i}", email=f"r{i}@e.com",
                      customer_segment="Loyal At Risk", churn_risk_score=0.72, total_spend_amount=6000.0, total_orders_count=3)
        for i in range(4)
    ]
    churn_opp = detect_churn_intervention_opportunity("m1", at_risk_custs)
    assert churn_opp is not None
    assert churn_opp.target_audience_count == 4

    # Basket builder opportunity
    low_basket_custs = [
        CustomerModel(id=f"lb_{i}", merchant_id="m1", name=f"Low {i}", email=f"l{i}@e.com",
                      customer_segment="Standard", churn_risk_score=0.30, total_spend_amount=3600.0, total_orders_count=4)
        for i in range(5)
    ]
    basket_opp = detect_aov_basket_builder_opportunity("m1", low_basket_custs, [])
    assert basket_opp is not None
    assert basket_opp.target_audience_count == 5
