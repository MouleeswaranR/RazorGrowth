import uuid
import random
from datetime import datetime, timedelta
from app.models.order import OrderModel
from app.models.product import ProductModel
from app.models.customer import CustomerModel

COHORT_ORDER_PROFILES = {
    "vip_active": {"min_orders": 8, "max_orders": 15, "recency_days": (1, 7), "prefer_expensive": True},
    "vip_dormant": {"min_orders": 6, "max_orders": 12, "recency_days": (35, 55), "prefer_expensive": True},
    "loyal": {"min_orders": 3, "max_orders": 6, "recency_days": (5, 30), "prefer_expensive": False},
    "new_recent": {"min_orders": 1, "max_orders": 2, "recency_days": (1, 14), "prefer_expensive": False},
    "at_risk": {"min_orders": 2, "max_orders": 4, "recency_days": (45, 70), "prefer_expensive": False},
    "one_time": {"min_orders": 1, "max_orders": 1, "recency_days": (40, 75), "prefer_expensive": False},
    "standard": {"min_orders": 2, "max_orders": 5, "recency_days": (10, 40), "prefer_expensive": False},
}

CATEGORY_PREFERENCES = {
    "vip_active": ["Footwear", "Outerwear"],
    "vip_dormant": ["Footwear", "Apparel"],
    "loyal": ["Apparel", "Accessories"],
    "new_recent": ["Apparel"],
    "at_risk": ["Apparel", "Footwear"],
    "one_time": ["Accessories"],
    "standard": ["Apparel", "Accessories"],
}


def _select_product_for_cohort(
    products: list[ProductModel],
    cohort: str,
) -> ProductModel:
    """Picks a product weighted by the cohort's category and price preferences."""
    preferred_categories = CATEGORY_PREFERENCES.get(cohort, ["Apparel"])
    prefer_expensive = COHORT_ORDER_PROFILES[cohort]["prefer_expensive"]

    preferred_products = [p for p in products if p.category in preferred_categories]
    if not preferred_products:
        preferred_products = products

    if prefer_expensive:
        preferred_products.sort(key=lambda p: p.price, reverse=True)
        weights = [i + 1 for i in range(len(preferred_products))]
        weights.reverse()
    else:
        weights = [1] * len(preferred_products)

    return random.choices(preferred_products, weights=weights, k=1)[0]


def _generate_order_timestamps(
    customer_created: datetime,
    cohort: str,
    order_count: int,
) -> list[datetime]:
    """Creates chronologically ordered timestamps matching the cohort's recency profile."""
    now = datetime.utcnow()
    recency_min, recency_max = COHORT_ORDER_PROFILES[cohort]["recency_days"]
    most_recent_order = now - timedelta(days=random.randint(recency_min, recency_max))

    if order_count == 1:
        return [most_recent_order]

    available_span = (most_recent_order - customer_created).days
    if available_span < 1:
        available_span = order_count

    timestamps = []
    for i in range(order_count):
        fraction = i / max(1, order_count - 1)
        day_offset = int(available_span * fraction)
        order_time = customer_created + timedelta(
            days=day_offset,
            hours=random.randint(8, 22),
            minutes=random.randint(0, 59),
        )
        timestamps.append(order_time)

    return sorted(timestamps)


def generate_synthetic_orders_batch(
    merchant_id: str,
    customers_with_cohorts: list[tuple[CustomerModel, str]],
    products: list[ProductModel],
    target_order_count: int = 2000,
) -> list[OrderModel]:
    """Generates orders distributed by cohort behavior with realistic product preferences."""
    orders: list[OrderModel] = []

    for customer, cohort in customers_with_cohorts:
        profile = COHORT_ORDER_PROFILES[cohort]
        num_orders = random.randint(profile["min_orders"], profile["max_orders"])
        timestamps = _generate_order_timestamps(customer.created_at, cohort, num_orders)

        for order_time in timestamps:
            product = _select_product_for_cohort(products, cohort)
            quantity = random.choices([1, 2, 3], weights=[0.80, 0.15, 0.05])[0]

            orders.append(
                OrderModel(
                    id=f"order_{uuid.uuid4().hex[:12]}",
                    merchant_id=merchant_id,
                    customer_id=customer.id,
                    product_id=product.id,
                    quantity=quantity,
                    amount=product.price * quantity,
                    status="completed",
                    created_at=order_time,
                )
            )

    return orders
