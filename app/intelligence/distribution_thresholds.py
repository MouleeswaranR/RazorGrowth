"""Computes distribution-aware quantile thresholds across merchant telemetry."""
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np

from app.models.customer import CustomerModel
from app.models.payment import PaymentModel


@dataclass
class MerchantDistributionThresholds:
    """Encapsulates empirical percentiles and normalization anchors for a merchant dataset."""
    vip_spend_p90: float
    loyal_orders_p75: float
    median_recency_days: float
    dormant_recency_p80: float
    rfm_spend_anchor_p95: float
    rfm_orders_anchor_p95: float
    rfm_recency_anchor_p95: float
    payment_benchmark_rate: float
    median_aov: float


def compute_merchant_distribution_thresholds(
    customers: list[CustomerModel],
    payments: list[PaymentModel] | None = None,
) -> MerchantDistributionThresholds:
    """Extracts empirical quantile thresholds from customer and payment population distributions."""
    if not customers:
        return _get_default_fallback_thresholds()

    now = datetime.now(timezone.utc)
    spends = [float(c.total_spend_amount) for c in customers]
    orders = [float(c.total_orders_count) for c in customers]
    
    recencies: list[float] = []
    aovs: list[float] = []
    for c in customers:
        if c.last_purchase_timestamp:
            ts = c.last_purchase_timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            days = max(0.0, (now - ts).total_seconds() / 86400.0)
            recencies.append(days)
        else:
            recencies.append(45.0)

        aov = float(c.total_spend_amount) / max(1.0, float(c.total_orders_count))
        aovs.append(aov)

    # Statistical percentiles with safe fallbacks for small sample sizes
    vip_spend_p90 = float(np.percentile(spends, 90)) if len(spends) >= 5 else max(3000.0, np.mean(spends) * 1.5)
    loyal_orders_p75 = float(np.percentile(orders, 75)) if len(orders) >= 5 else max(2.0, np.median(orders))
    median_recency = float(np.percentile(recencies, 50)) if len(recencies) >= 5 else 30.0
    dormant_recency_p80 = float(np.percentile(recencies, 80)) if len(recencies) >= 5 else max(30.0, median_recency * 1.5)

    rfm_spend_anchor = float(np.percentile(spends, 95)) if len(spends) >= 5 else max(5000.0, vip_spend_p90 * 1.2)
    rfm_orders_anchor = float(np.percentile(orders, 95)) if len(orders) >= 5 else max(5.0, loyal_orders_p75 * 1.5)
    rfm_recency_anchor = float(np.percentile(recencies, 95)) if len(recencies) >= 5 else 90.0

    # Payment benchmark extraction
    payment_benchmark = 0.92
    if payments and len(payments) >= 10:
        methods = set(p.payment_method for p in payments)
        rates: list[float] = []
        for m in methods:
            m_payments = [p for p in payments if p.payment_method == m]
            if len(m_payments) >= 3:
                success_count = sum(1 for p in m_payments if p.status == "captured")
                rates.append(success_count / len(m_payments))
        if rates:
            payment_benchmark = float(np.percentile(rates, 75))
            payment_benchmark = max(0.80, min(0.98, payment_benchmark))

    median_aov = float(np.percentile(aovs, 50)) if aovs else 1500.0

    return MerchantDistributionThresholds(
        vip_spend_p90=max(500.0, vip_spend_p90),
        loyal_orders_p75=max(2.0, loyal_orders_p75),
        median_recency_days=max(7.0, median_recency),
        dormant_recency_p80=max(14.0, dormant_recency_p80),
        rfm_spend_anchor_p95=max(1000.0, rfm_spend_anchor),
        rfm_orders_anchor_p95=max(3.0, rfm_orders_anchor),
        rfm_recency_anchor_p95=max(30.0, rfm_recency_anchor),
        payment_benchmark_rate=payment_benchmark,
        median_aov=max(200.0, median_aov),
    )


def _get_default_fallback_thresholds() -> MerchantDistributionThresholds:
    """Provides conservative default thresholds when customer dataset is empty."""
    return MerchantDistributionThresholds(
        vip_spend_p90=5000.0,
        loyal_orders_p75=3.0,
        median_recency_days=25.0,
        dormant_recency_p80=45.0,
        rfm_spend_anchor_p95=10000.0,
        rfm_orders_anchor_p95=6.0,
        rfm_recency_anchor_p95=90.0,
        payment_benchmark_rate=0.92,
        median_aov=1800.0,
    )
