"""Computes customer churn risk scores using continuous recency decay and spend trajectory."""
from datetime import datetime, timezone
from app.models.customer import CustomerModel
from app.models.order import OrderModel
from app.intelligence.distribution_thresholds import (
    MerchantDistributionThresholds,
    _get_default_fallback_thresholds,
)


def calculate_churn_risk_score(
    customer: CustomerModel,
    thresholds: MerchantDistributionThresholds | None = None,
) -> float:
    """Calculates churn risk between 0.0-1.0 using continuous distribution-aware recency decay."""
    recency_risk = _compute_recency_risk(customer, thresholds)
    return round(recency_risk, 3)


def calculate_churn_risk_with_orders(
    customer: CustomerModel,
    orders: list[OrderModel],
    thresholds: MerchantDistributionThresholds | None = None,
) -> float:
    """Computes enhanced churn risk factoring in purchase interval decay and spend trajectory."""
    recency_risk = _compute_recency_risk(customer, thresholds)
    frequency_decay_risk = _compute_frequency_decay_risk(orders)
    spend_decline_risk = _compute_spend_decline_risk(orders)

    # Weighted composite: 50% recency, 30% frequency decay, 20% spend decline
    weighted_risk = (0.50 * recency_risk) + (0.30 * frequency_decay_risk) + (0.20 * spend_decline_risk)
    return round(min(1.0, max(0.0, weighted_risk)), 3)


def _compute_recency_risk(
    customer: CustomerModel,
    thresholds: MerchantDistributionThresholds | None = None,
) -> float:
    """Scores churn risk from 0.0-1.0 via smooth continuous CDF against merchant recency distribution."""
    if not customer.last_purchase_timestamp:
        return 0.90

    thresh = thresholds or _get_default_fallback_thresholds()
    now = datetime.now(timezone.utc)
    ts = customer.last_purchase_timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    days_inactive = max(0.0, (now - ts).total_seconds() / 86400.0)

    # Smooth continuous curve anchored to merchant median and 80th-percentile dormancy
    # Low risk when under median, steep rise toward 1.0 as it passes 80th-percentile
    dormant_anchor = max(14.0, thresh.dormant_recency_p80 * 1.25)
    normalized_recency = days_inactive / dormant_anchor

    return min(1.0, max(0.02, round(normalized_recency ** 1.15, 3)))


def _compute_frequency_decay_risk(orders: list[OrderModel]) -> float:
    """Detects whether the gap between consecutive purchases is growing over time."""
    if len(orders) < 3:
        return 0.50

    sorted_orders = sorted(orders, key=lambda o: o.created_at)
    gaps = [
        max(1.0, float((sorted_orders[i + 1].created_at - sorted_orders[i].created_at).total_seconds() / 86400.0))
        for i in range(len(sorted_orders) - 1)
    ]

    if len(gaps) < 2:
        return 0.50

    midpoint = len(gaps) // 2
    first_half_avg = sum(gaps[:midpoint]) / max(1, midpoint)
    second_half_avg = sum(gaps[midpoint:]) / max(1, len(gaps) - midpoint)

    if first_half_avg <= 0.0:
        return 0.50

    decay_ratio = second_half_avg / first_half_avg
    # Smooth continuous frequency decay scaling
    return round(min(1.0, max(0.05, 0.35 * decay_ratio)), 3)


def _compute_spend_decline_risk(orders: list[OrderModel]) -> float:
    """Detects whether average order value is declining in the recent half of order history."""
    if len(orders) < 4:
        return 0.30

    sorted_orders = sorted(orders, key=lambda o: o.created_at)
    midpoint = len(sorted_orders) // 2
    early_avg = sum(o.amount for o in sorted_orders[:midpoint]) / max(1, midpoint)
    recent_avg = sum(o.amount for o in sorted_orders[midpoint:]) / max(1, len(sorted_orders) - midpoint)

    if early_avg <= 0.0:
        return 0.30

    spend_ratio = recent_avg / early_avg
    # Continuous spend decay: 1.0 ratio -> 0.05 risk; 0.5 ratio -> 0.70 risk
    risk = max(0.05, min(0.95, 1.05 - spend_ratio))
    return round(risk, 3)
