from app.models.order import OrderModel, PAID_ORDER_STATUSES


def calculate_customer_order_metrics(orders: list[OrderModel]) -> dict:
    """Computes total spend, order count, and latest purchase timestamp from paid order history.

    Only orders in PAID_ORDER_STATUSES are counted. Campaign launches create
    "pending_checkout" orders for the treatment cohort that are never paid unless the
    customer converts; counting those would inflate spend and reset recency, which in
    turn would flip a targeted dormant customer back to "active" and erase the very
    opportunity that selected them.
    """
    paid_orders = [order for order in orders if order.status in PAID_ORDER_STATUSES]

    if not paid_orders:
        return {
            "total_orders_count": 0,
            "total_spend_amount": 0.0,
            "last_purchase_timestamp": None,
        }

    sorted_orders = sorted(paid_orders, key=lambda o: o.created_at, reverse=True)

    return {
        "total_orders_count": len(paid_orders),
        "total_spend_amount": sum(order.amount for order in paid_orders),
        "last_purchase_timestamp": sorted_orders[0].created_at,
    }
