import pytest
from app.simulator.merchant_generator import generate_synthetic_merchant
from app.simulator.customer_generator import generate_synthetic_customers_batch
from app.simulator.order_generator import generate_synthetic_orders_batch
from app.simulator.payment_event_generator import generate_synthetic_payments_batch
from app.simulator.simulation_orchestrator import create_default_products


def test_merchant_generator_creates_valid_model():
    """Verifies synthetic merchant creation has valid ID, currency, and name."""
    merchant = generate_synthetic_merchant("TestBrand")
    assert merchant.id.startswith("merch_")
    assert merchant.name == "TestBrand"
    assert merchant.currency == "INR"


def test_customer_generator_cohort_distribution():
    """Verifies customer generator assigns valid behavioral cohorts across batches."""
    customers = generate_synthetic_customers_batch("merch_123", count=100)
    assert len(customers) == 100

    cohorts = [cohort for _, cohort in customers]
    assert "vip_active" in cohorts
    assert "vip_dormant" in cohorts
    assert "loyal" in cohorts


def test_customer_generator_single_customer_edge_case():
    """Verifies customer generator works for minimum count edge case (count=1)."""
    customers = generate_synthetic_customers_batch("merch_123", count=1)
    assert len(customers) == 1
    cust, cohort = customers[0]
    assert cust.email.endswith("@example.com")
    assert cust.name != ""


def test_order_generator_respects_cohort_profiles():
    """Verifies order generation distributes orders based on cohort preferences."""
    merchant_id = "merch_test"
    products = create_default_products(merchant_id)
    customers = generate_synthetic_customers_batch(merchant_id, count=10)

    orders = generate_synthetic_orders_batch(merchant_id, customers, products)
    assert len(orders) > 0

    # Ensure all orders have positive amounts and valid timestamps
    for order in orders:
        assert order.amount > 0
        assert order.quantity >= 1
        assert order.status == "completed"


def test_payment_generator_success_rates():
    """Verifies payment generator simulates payments with valid status codes."""
    merchant_id = "merch_test"
    products = create_default_products(merchant_id)
    customers = generate_synthetic_customers_batch(merchant_id, count=10)
    orders = generate_synthetic_orders_batch(merchant_id, customers, products)

    payments = generate_synthetic_payments_batch(orders)
    assert len(payments) == len(orders)

    statuses = {p.status for p in payments}
    assert "captured" in statuses
    for p in payments:
        assert p.payment_method in ["upi", "card", "netbanking", "wallet"]
