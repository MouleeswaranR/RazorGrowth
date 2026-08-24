"""Intelligence layer package for segmentation, churn scoring, and opportunity detection."""
from app.intelligence.customer_segmentation import classify_customer_segment, compute_rfm_composite_score
from app.intelligence.churn_predictor import calculate_churn_risk_score, calculate_churn_risk_with_orders
from app.intelligence.clv_estimator import estimate_customer_lifetime_value
from app.intelligence.product_recommender import build_category_copurchase_matrix, find_cross_sell_candidates
from app.intelligence.opportunity_detector import detect_all_opportunities
from app.intelligence.payment_method_analyzer import analyze_payment_method_performance

__all__ = [
    "classify_customer_segment",
    "compute_rfm_composite_score",
    "calculate_churn_risk_score",
    "calculate_churn_risk_with_orders",
    "estimate_customer_lifetime_value",
    "build_category_copurchase_matrix",
    "find_cross_sell_candidates",
    "detect_all_opportunities",
    "analyze_payment_method_performance",
]
