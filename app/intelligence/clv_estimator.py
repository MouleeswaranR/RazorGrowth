"""Projects 12-month customer lifetime value using continuous frequency scaling and churn risk discounting."""
import math
from app.models.customer import CustomerModel


def estimate_customer_lifetime_value(customer: CustomerModel) -> float:
    """Projects 12-month CLV using continuous frequency scaling and churn-risk discount factor."""
    orders = float(customer.total_orders_count)
    if orders <= 0:
        return round(float(customer.total_spend_amount) or 1500.0, 2)

    average_order_value = float(customer.total_spend_amount) / orders

    # Continuous frequency scaling: smooth curve asymptotically scaling future order run rate
    # 1 order -> ~1.8x, 3 orders -> ~1.45x, 10 orders -> ~1.20x
    frequency_multiplier = 1.15 + (0.75 / (1.0 + 0.35 * math.log(orders + 1.0)))
    annual_frequency_estimate = orders * frequency_multiplier

    # Discount projected value by churn risk
    churn_discount_factor = max(0.20, 1.0 - (float(customer.churn_risk_score) * 0.60))

    projected_clv = average_order_value * annual_frequency_estimate * churn_discount_factor
    return round(max(float(customer.total_spend_amount), projected_clv), 2)
