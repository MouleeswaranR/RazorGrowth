from datetime import datetime
from app.models.order import OrderModel


def calculate_customer_order_metrics(orders: list[OrderModel]) -> dict:
    """Computes total spend, order count, and latest purchase timestamp from order history."""
    if not orders:
        return {
            "total_orders_count": 0,
            "total_spend_amount": 0.0,
            "last_purchase_timestamp": None,
        }

    total_orders = len(orders)
    total_spend = sum(order.amount for order in orders)
    sorted_orders = sorted(orders, key=lambda o: o.created_at, reverse=True)
    latest_order_time = sorted_orders[0].created_at

    return {
        "total_orders_count": total_orders,
        "total_spend_amount": total_spend,
        "last_purchase_timestamp": latest_order_time,
    }
