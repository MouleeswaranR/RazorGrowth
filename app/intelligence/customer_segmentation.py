"""Segments customers into behavioral cohorts using distribution-aware RFM quantiles."""
from datetime import datetime, timezone
from app.models.customer import CustomerModel
from app.intelligence.distribution_thresholds import (
    MerchantDistributionThresholds,
    _get_default_fallback_thresholds,
)


def classify_customer_segment(
    customer: CustomerModel,
    thresholds: MerchantDistributionThresholds | None = None,
) -> str:
    """Classifies a customer into behavioral segments using empirical population quantiles."""
    thresh = thresholds or _get_default_fallback_thresholds()
    now = datetime.now(timezone.utc)

    days_since_last_purchase = 999.0
    if customer.last_purchase_timestamp:
        ts = customer.last_purchase_timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        days_since_last_purchase = max(0.0, (now - ts).total_seconds() / 86400.0)

    spend = float(customer.total_spend_amount)
    orders = int(customer.total_orders_count)

    if orders == 0:
        return "Standard"

    # VIP Segment: Top 10% spend distribution
    if spend >= thresh.vip_spend_p90:
        if days_since_last_purchase <= thresh.median_recency_days:
            return "VIP Active"
        return "VIP Dormant"

    # Loyal Segment: Top 25% frequency distribution
    if orders >= thresh.loyal_orders_p75:
        if days_since_last_purchase <= thresh.median_recency_days:
            return "Loyal"
        if days_since_last_purchase <= thresh.dormant_recency_p80:
            return "Loyal At Risk"
        return "At Risk"

    # Single-order shoppers
    if orders == 1:
        if days_since_last_purchase <= max(14.0, thresh.median_recency_days * 0.6):
            return "New"
        if days_since_last_purchase > thresh.dormant_recency_p80:
            return "One-Time"
        return "Standard"

    if days_since_last_purchase > thresh.dormant_recency_p80:
        return "At Risk"

    return "Standard"


def compute_rfm_composite_score(
    customer: CustomerModel,
    thresholds: MerchantDistributionThresholds | None = None,
) -> float:
    """Computes a normalized 0.0-1.0 composite score against population quantile anchors."""
    thresh = thresholds or _get_default_fallback_thresholds()
    now = datetime.now(timezone.utc)

    days_since = 999.0
    if customer.last_purchase_timestamp:
        ts = customer.last_purchase_timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        days_since = max(0.0, (now - ts).total_seconds() / 86400.0)

    # Recency score: normalized against 95th percentile recency
    recency_score = max(0.0, 1.0 - (days_since / max(30.0, thresh.rfm_recency_anchor_p95)))

    # Frequency score: normalized against 95th percentile orders anchor
    frequency_score = min(1.0, float(customer.total_orders_count) / max(1.0, thresh.rfm_orders_anchor_p95))

    # Monetary score: normalized against 95th percentile spend anchor
    monetary_score = min(1.0, float(customer.total_spend_amount) / max(1.0, thresh.rfm_spend_anchor_p95))

    return round(0.40 * recency_score + 0.35 * frequency_score + 0.25 * monetary_score, 3)
