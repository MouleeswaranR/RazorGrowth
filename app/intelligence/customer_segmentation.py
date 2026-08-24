from datetime import datetime
from app.models.customer import CustomerModel


def classify_customer_segment(customer: CustomerModel) -> str:
    """Classifies a customer into behavioral segments using RFM-weighted heuristics."""
    now = datetime.utcnow()
    days_since_last_purchase = 999
    if customer.last_purchase_timestamp:
        days_since_last_purchase = (now - customer.last_purchase_timestamp).days

    spend = customer.total_spend_amount
    orders = customer.total_orders_count

    if orders == 0:
        return "Standard"
    if spend >= 10000 and days_since_last_purchase <= 30:
        return "VIP Active"
    if spend >= 5000 and days_since_last_purchase > 30:
        return "VIP Dormant"
    if orders >= 3 and days_since_last_purchase <= 30:
        return "Loyal"
    if orders >= 3 and 30 < days_since_last_purchase <= 60:
        return "Loyal At Risk"
    if orders == 1 and days_since_last_purchase <= 14:
        return "New"
    if orders == 1 and days_since_last_purchase > 40:
        return "One-Time"
    if days_since_last_purchase > 60:
        return "At Risk"
    return "Standard"



def compute_rfm_composite_score(customer: CustomerModel) -> float:
    """Computes a normalized 0.0-1.0 composite score weighting Recency, Frequency, and Monetary."""
    now = datetime.utcnow()
    days_since = 999
    if customer.last_purchase_timestamp:
        days_since = (now - customer.last_purchase_timestamp).days

    # Recency score: 1.0 if purchased today, decays toward 0.0 at 90+ days
    recency_score = max(0.0, 1.0 - (days_since / 90.0))

    # Frequency score: normalized against benchmark of 10 orders
    frequency_score = min(1.0, customer.total_orders_count / 10.0)

    # Monetary score: normalized against benchmark of ₹25,000 total spend
    monetary_score = min(1.0, customer.total_spend_amount / 25000.0)

    return round(0.40 * recency_score + 0.35 * frequency_score + 0.25 * monetary_score, 3)
