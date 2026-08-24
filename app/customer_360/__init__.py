"""Customer 360 profile aggregation and lifetime metrics package."""
from app.customer_360.metric_calculator import calculate_customer_order_metrics
from app.customer_360.profile_builder import refresh_customer_360_profile

__all__ = [
    "calculate_customer_order_metrics",
    "refresh_customer_360_profile",
]
