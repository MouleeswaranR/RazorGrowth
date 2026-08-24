"""Discovers actionable revenue opportunities using distribution-aware analytical intelligence."""
import uuid
from app.models.customer import CustomerModel
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.models.opportunity import OpportunityModel
from app.intelligence.distribution_thresholds import (
    MerchantDistributionThresholds,
    compute_merchant_distribution_thresholds,
    _get_default_fallback_thresholds,
)
from app.intelligence.product_recommender import (
    build_category_copurchase_matrix,
    find_cross_sell_candidates,
)
from app.intelligence.payment_method_analyzer import (
    analyze_payment_method_performance,
    find_underperforming_payment_methods,
)


def detect_dormant_vip_opportunity(
    merchant_id: str,
    customers: list[CustomerModel],
    thresholds: MerchantDistributionThresholds | None = None,
) -> OpportunityModel | None:
    """Discovers re-engagement opportunity for dormant high-value customers using dynamic spend percentiles."""
    thresh = thresholds or compute_merchant_distribution_thresholds(customers)
    
    dormant_vips = [
        c for c in customers
        if (c.customer_segment in ("VIP Dormant", "Loyal At Risk") or (float(c.churn_risk_score) >= 0.45 and float(c.total_spend_amount) >= thresh.vip_spend_p90 * 0.70))
        and float(c.total_spend_amount) >= thresh.vip_spend_p90 * 0.60
    ]
    if len(dormant_vips) < 2:
        return None

    avg_aov = sum(float(c.total_spend_amount) / max(1.0, float(c.total_orders_count)) for c in dormant_vips) / len(dormant_vips)
    estimated_gmv = len(dormant_vips) * avg_aov * 0.70

    vip_concentration = len(dormant_vips) / max(1, len(customers))
    confidence = round(min(0.92, max(0.60, 0.60 + vip_concentration * 1.5)), 2)

    return OpportunityModel(
        id=f"opp_{uuid.uuid4().hex[:12]}",
        merchant_id=merchant_id,
        title="Dormant High-Value Customer Recovery",
        opportunity_type="customer_churn_prevention",
        description=(
            f"{len(dormant_vips)} high-value customers (top spend quantile ≥ ₹{thresh.vip_spend_p90 * 0.60:,.0f}) haven't purchased recently. "
            f"Average historical AOV: ₹{avg_aov:,.0f}. Personalized re-engagement recommended."
        ),
        target_audience_count=len(dormant_vips),
        estimated_gmv_impact=round(estimated_gmv, 2),
        confidence_score=confidence,
        status="detected",
    )


def detect_cross_sell_opportunity(
    merchant_id: str,
    orders: list[OrderModel],
    product_category_map: dict[str, str],
    customers_map: dict[str, CustomerModel],
    thresholds: MerchantDistributionThresholds | None = None,
) -> OpportunityModel | None:
    """Discovers cross-sell opportunity from co-purchase affinity analysis."""
    affinity_matrix = build_category_copurchase_matrix(orders, product_category_map)
    if not affinity_matrix:
        return None

    best_source = None
    best_target = None
    best_confidence = 0.0

    for source_cat, targets in affinity_matrix.items():
        for target_cat, confidence in targets:
            if confidence > best_confidence:
                best_confidence = confidence
                best_source = source_cat
                best_target = target_cat

    if not best_source or best_confidence < 0.05:
        return None

    candidate_ids = find_cross_sell_candidates(orders, product_category_map, best_source, best_target)
    active_candidates = [
        cid for cid in candidate_ids
        if cid in customers_map and float(customers_map[cid].churn_risk_score) < 0.90
    ]

    if len(active_candidates) < 1:
        return None

    thresh = thresholds or _get_default_fallback_thresholds()
    estimated_gmv = len(active_candidates) * thresh.median_aov * max(0.20, best_confidence)

    return OpportunityModel(
        id=f"opp_{uuid.uuid4().hex[:12]}",
        merchant_id=merchant_id,
        title=f"Cross-Sell {best_source} → {best_target}",
        opportunity_type="cross_sell_affinity",
        description=(
            f"{len(active_candidates)} customers who bought {best_source} have not purchased {best_target}. "
            f"Co-purchase confidence: {best_confidence:.0%}."
        ),
        target_audience_count=len(active_candidates),
        estimated_gmv_impact=round(estimated_gmv, 2),
        confidence_score=round(max(0.65, best_confidence), 2),
        status="detected",
    )


def _payment_confidence(current: float, benchmark: float) -> float:
    gap = max(0.0, benchmark - current)
    return round(min(0.95, 0.50 + (gap * 2.0)), 2)


def detect_payment_optimization_opportunity(
    merchant_id: str,
    payments: list[PaymentModel],
    thresholds: MerchantDistributionThresholds | None = None,
) -> OpportunityModel | None:
    """Discovers revenue recovery opportunity from underperforming payment methods against merchant baseline."""
    thresh = thresholds or _get_default_fallback_thresholds()
    method_stats = analyze_payment_method_performance(payments)
    underperformers = find_underperforming_payment_methods(method_stats, thresholds=thresh)

    if not underperformers:
        return None

    worst = underperformers[0]
    total_recoverable = sum(u["recoverable_gmv"] for u in underperformers)
    failed_attempts_count = worst.get("failed_count", sum(1 for p in payments if p.payment_method == worst["method"] and p.status == "failed"))

    return OpportunityModel(
        id=f"opp_{uuid.uuid4().hex[:12]}",
        merchant_id=merchant_id,
        title=f"Payment Method Optimization ({worst['method'].upper()})",
        opportunity_type="payment_optimization",
        description=(
            f"{worst['method'].upper()} has a {worst['current_rate']:.1%} success rate "
            f"vs {worst['benchmark_rate']:.1%} merchant benchmark baseline. "
            f"₹{worst['estimated_lost_gmv']:,.0f} lost across {failed_attempts_count} failed checkout attempts. "
            f"Recommend automatic UPI retry prompts and checkout nudges."
        ),
        target_audience_count=max(1, failed_attempts_count),
        estimated_gmv_impact=round(total_recoverable, 2),
        confidence_score=_payment_confidence(worst["current_rate"], worst["benchmark_rate"]),
        status="detected",
    )


def detect_churn_intervention_opportunity(
    merchant_id: str,
    customers: list[CustomerModel],
    thresholds: MerchantDistributionThresholds | None = None,
) -> OpportunityModel | None:
    """Discovers proactive retention opportunity for at-risk customers before they become dormant."""
    at_risk_candidates = [
        c for c in customers
        if 0.40 <= float(c.churn_risk_score) < 0.90
        and int(c.total_orders_count) >= 1
    ]
    if len(at_risk_candidates) < 2:
        return None

    avg_spend = sum(float(c.total_spend_amount) for c in at_risk_candidates) / len(at_risk_candidates)
    est_gmv = len(at_risk_candidates) * avg_spend * 0.40
    confidence = round(min(0.88, 0.60 + (len(at_risk_candidates) / max(1, len(customers))) * 1.8), 2)

    return OpportunityModel(
        id=f"opp_{uuid.uuid4().hex[:12]}",
        merchant_id=merchant_id,
        title="Proactive Churn Intervention",
        opportunity_type="customer_churn_prevention",
        description=(
            f"{len(at_risk_candidates)} repeat shoppers exhibit expanding purchase intervals and elevated churn risk (40%-90%). "
            f"Proactive time-sensitive retention nudge can safeguard ₹{est_gmv:,.0f} in annual customer lifetime value."
        ),
        target_audience_count=len(at_risk_candidates),
        estimated_gmv_impact=round(est_gmv, 2),
        confidence_score=confidence,
        status="detected",
    )


def detect_aov_basket_builder_opportunity(
    merchant_id: str,
    customers: list[CustomerModel],
    orders: list[OrderModel],
    thresholds: MerchantDistributionThresholds | None = None,
) -> OpportunityModel | None:
    """Discovers basket expansion opportunity for high-frequency shoppers with below-average order values."""
    thresh = thresholds or compute_merchant_distribution_thresholds(customers)

    frequent_low_basket = [
        c for c in customers
        if int(c.total_orders_count) >= 2
        and (float(c.total_spend_amount) / max(1.0, float(c.total_orders_count))) < thresh.median_aov * 1.25
        and float(c.churn_risk_score) < 0.75
    ]
    if len(frequent_low_basket) < 2:
        return None

    current_aov = sum(float(c.total_spend_amount) for c in frequent_low_basket) / sum(max(1, int(c.total_orders_count)) for c in frequent_low_basket)
    target_aov = current_aov * 1.35
    incremental_per_order = target_aov - current_aov
    est_gmv = len(frequent_low_basket) * 2 * incremental_per_order

    return OpportunityModel(
        id=f"opp_{uuid.uuid4().hex[:12]}",
        merchant_id=merchant_id,
        title="Tiered Minimum Spend Basket Builder",
        opportunity_type="cross_sell_affinity",
        description=(
            f"{len(frequent_low_basket)} active frequent customers average ₹{current_aov:,.0f} per order below store median AOV (₹{thresh.median_aov:,.0f}). "
            f"Deploying a spend threshold voucher is estimated to unlock ₹{est_gmv:,.0f} in incremental basket expansion."
        ),
        target_audience_count=len(frequent_low_basket),
        estimated_gmv_impact=round(est_gmv, 2),
        confidence_score=0.82,
        status="detected",
    )


def detect_all_opportunities(
    merchant_id: str,
    customers: list[CustomerModel],
    orders: list[OrderModel],
    payments: list[PaymentModel],
    product_category_map: dict[str, str],
) -> list[OpportunityModel]:
    """Runs all 5 distribution-aware opportunity detection engines and returns discovered opportunities."""
    thresholds = compute_merchant_distribution_thresholds(customers, payments)
    customers_map = {c.id: c for c in customers}
    opportunities: list[OpportunityModel] = []

    dormant_opp = detect_dormant_vip_opportunity(merchant_id, customers, thresholds)
    if dormant_opp:
        opportunities.append(dormant_opp)

    cross_sell_opp = detect_cross_sell_opportunity(
        merchant_id, orders, product_category_map, customers_map, thresholds,
    )
    if cross_sell_opp:
        opportunities.append(cross_sell_opp)

    payment_opp = detect_payment_optimization_opportunity(merchant_id, payments, thresholds)
    if payment_opp:
        opportunities.append(payment_opp)

    churn_intervene = detect_churn_intervention_opportunity(merchant_id, customers, thresholds)
    if churn_intervene:
        opportunities.append(churn_intervene)

    basket_builder = detect_aov_basket_builder_opportunity(merchant_id, customers, orders, thresholds)
    if basket_builder:
        opportunities.append(basket_builder)

    return opportunities
