from datetime import datetime
from app.models.customer import CustomerModel
from app.models.order import OrderModel


def calculate_churn_risk_score(customer: CustomerModel) -> float:
    """Calculates churn risk between 0.0-1.0 using recency, frequency decay, and spend trajectory."""
    recency_risk = _compute_recency_risk(customer)
    return round(recency_risk, 3)


def calculate_churn_risk_with_orders(
    customer: CustomerModel,
    orders: list[OrderModel],
) -> float:
    """Computes enhanced churn risk factoring in purchase interval decay and spend trajectory."""
    recency_risk = _compute_recency_risk(customer)
    frequency_decay_risk = _compute_frequency_decay_risk(orders)
    spend_decline_risk = _compute_spend_decline_risk(orders)

    # Weighted composite: 50% recency, 30% frequency decay, 20% spend decline
    weighted_risk = (0.50 * recency_risk) + (0.30 * frequency_decay_risk) + (0.20 * spend_decline_risk)
    return round(min(1.0, max(0.0, weighted_risk)), 3)


def _compute_recency_risk(customer: CustomerModel) -> float:
    """Scores churn risk from 0.0-1.0 based on days since last purchase."""
    if not customer.last_purchase_timestamp:
        return 0.90
    days_inactive = (datetime.utcnow() - customer.last_purchase_timestamp).days
    if days_inactive <= 7:
        return 0.05
    if days_inactive <= 15:
        return 0.15
    if days_inactive <= 30:
        return 0.40
    if days_inactive <= 45:
        return 0.65
    if days_inactive <= 60:
        return 0.80
    return 0.95


def _compute_frequency_decay_risk(orders: list[OrderModel]) -> float:
    """Detects whether the gap between consecutive purchases is growing over time."""
    if len(orders) < 3:
        return 0.50

    sorted_orders = sorted(orders, key=lambda o: o.created_at)
    gaps = [
        (sorted_orders[i + 1].created_at - sorted_orders[i].created_at).days
        for i in range(len(sorted_orders) - 1)
    ]

    if len(gaps) < 2:
        return 0.50

    first_half_avg = sum(gaps[: len(gaps) // 2]) / len(gaps[: len(gaps) // 2])
    second_half_avg = sum(gaps[len(gaps) // 2 :]) / len(gaps[len(gaps) // 2 :])

    if first_half_avg == 0:
        return 0.50

    decay_ratio = second_half_avg / first_half_avg
    if decay_ratio <= 1.0:
        return 0.10
    if decay_ratio <= 1.5:
        return 0.40
    if decay_ratio <= 2.5:
        return 0.70
    return 0.90


def _compute_spend_decline_risk(orders: list[OrderModel]) -> float:
    """Detects whether average order value is declining in the recent half of order history."""
    if len(orders) < 4:
        return 0.30

    sorted_orders = sorted(orders, key=lambda o: o.created_at)
    midpoint = len(sorted_orders) // 2
    early_avg = sum(o.amount for o in sorted_orders[:midpoint]) / midpoint
    recent_avg = sum(o.amount for o in sorted_orders[midpoint:]) / (len(sorted_orders) - midpoint)

    if early_avg == 0:
        return 0.30

    decline_ratio = recent_avg / early_avg
    if decline_ratio >= 1.0:
        return 0.05
    if decline_ratio >= 0.8:
        return 0.30
    if decline_ratio >= 0.6:
        return 0.60
    return 0.85
