from app.models.customer import CustomerModel


def estimate_customer_lifetime_value(customer: CustomerModel) -> float:
    """Projects 12-month CLV using AOV, frequency, and churn-risk discount factor."""
    if customer.total_orders_count == 0:
        return 1500.0

    average_order_value = customer.total_spend_amount / customer.total_orders_count
    historical_frequency = customer.total_orders_count

    # Project forward: customers with more history get a more conservative multiplier
    if historical_frequency >= 8:
        annual_frequency_estimate = historical_frequency * 1.2
    elif historical_frequency >= 3:
        annual_frequency_estimate = historical_frequency * 1.5
    else:
        annual_frequency_estimate = historical_frequency * 2.0

    # Discount projected value by churn risk
    churn_discount_factor = 1.0 - (customer.churn_risk_score * 0.6)

    projected_clv = average_order_value * annual_frequency_estimate * churn_discount_factor
    return round(max(0.0, projected_clv), 2)
