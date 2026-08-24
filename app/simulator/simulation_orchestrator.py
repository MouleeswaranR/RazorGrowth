import uuid
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import MerchantModel
from app.models.product import ProductModel
from app.models.customer import CustomerModel
from app.models.order import OrderModel
from app.simulator.merchant_generator import generate_synthetic_merchant
from app.simulator.customer_generator import generate_synthetic_customers_batch
from app.simulator.order_generator import generate_synthetic_orders_batch
from app.simulator.payment_event_generator import generate_synthetic_payments_batch
from app.intelligence.customer_segmentation import classify_customer_segment
from app.intelligence.churn_predictor import calculate_churn_risk_score
from app.intelligence.clv_estimator import estimate_customer_lifetime_value
from app.services.snapshot_storage_service import snapshot_storage_service

DEFAULT_PRODUCTS = [
    {"title": "Classic Cotton T-Shirt", "category": "Apparel", "price": 999.0},
    {"title": "Performance Running Shoes", "category": "Footwear", "price": 2999.0},
    {"title": "Slim Fit Denim Jeans", "category": "Apparel", "price": 1999.0},
    {"title": "Waterproof Outdoor Jacket", "category": "Outerwear", "price": 4999.0},
    {"title": "Cotton Sports Socks Pack", "category": "Accessories", "price": 499.0},
]


def create_default_products(merchant_id: str) -> list[ProductModel]:
    """Instantiates product catalog models for the simulated merchant."""
    return [
        ProductModel(
            id=f"prod_{uuid.uuid4().hex[:10]}",
            merchant_id=merchant_id,
            title=item["title"],
            category=item["category"],
            price=item["price"],
        )
        for item in DEFAULT_PRODUCTS
    ]


def _enrich_customer_360_from_orders(
    customer: CustomerModel,
    customer_orders: list[OrderModel],
    product_map: dict[str, ProductModel],
) -> None:
    """Populates Customer 360 metrics, segment, churn score, and CLV from order history."""
    if not customer_orders:
        return

    customer.total_orders_count = len(customer_orders)
    customer.total_spend_amount = sum(o.amount for o in customer_orders)

    sorted_orders = sorted(customer_orders, key=lambda o: o.created_at, reverse=True)
    customer.last_purchase_timestamp = sorted_orders[0].created_at

    category_counts = Counter(
        product_map[o.product_id].category
        for o in customer_orders
        if o.product_id in product_map
    )
    if category_counts:
        customer.favorite_category = category_counts.most_common(1)[0][0]

    customer.customer_segment = classify_customer_segment(customer)
    customer.churn_risk_score = calculate_churn_risk_score(customer)
    customer.predicted_lifetime_value = estimate_customer_lifetime_value(customer)

    aov = customer.total_spend_amount / customer.total_orders_count
    frequency_factor = min(1.0, customer.total_orders_count / 10.0)
    recency_factor = 1.0 - customer.churn_risk_score
    customer.repurchase_probability = round(
        0.4 * frequency_factor + 0.4 * recency_factor + 0.2 * min(1.0, aov / 5000.0),
        3,
    )


async def run_full_merchant_simulation(
    session: AsyncSession,
    merchant_name: str = "StyleKart",
    customer_count: int = 500,
    order_count: int = 2000,
) -> dict:
    """Generates synthetic merchant data, enriches Customer 360, and saves a local JSON snapshot."""
    merchant: MerchantModel = generate_synthetic_merchant(merchant_name)
    session.add(merchant)
    await session.flush()

    products = create_default_products(merchant.id)
    session.add_all(products)
    await session.flush()

    customers_with_cohorts = generate_synthetic_customers_batch(merchant.id, customer_count)
    customer_models = [c for c, _ in customers_with_cohorts]
    session.add_all(customer_models)
    await session.flush()

    orders = generate_synthetic_orders_batch(merchant.id, customers_with_cohorts, products)
    session.add_all(orders)
    await session.flush()

    payments = generate_synthetic_payments_batch(orders)
    session.add_all(payments)
    await session.flush()

    product_map = {p.id: p for p in products}
    orders_by_customer: dict[str, list[OrderModel]] = {}
    for order in orders:
        orders_by_customer.setdefault(order.customer_id, []).append(order)

    segment_distribution: dict[str, int] = Counter()
    for customer in customer_models:
        _enrich_customer_360_from_orders(
            customer, orders_by_customer.get(customer.id, []), product_map
        )
        segment_distribution[customer.customer_segment] += 1

    await session.commit()

    result = {
        "merchant_id": merchant.id,
        "merchant_name": merchant_name,
        "customers_created": len(customer_models),
        "products_created": len(products),
        "orders_created": len(orders),
        "payments_created": len(payments),
        "segment_distribution": dict(segment_distribution),
        "products": [{"id": p.id, "title": p.title, "category": p.category, "price": p.price} for p in products],
        "sample_customers": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "location": c.location,
                "segment": c.customer_segment,
                "total_spend": c.total_spend_amount,
                "total_orders": c.total_orders_count,
                "churn_risk": c.churn_risk_score,
                "clv": c.predicted_lifetime_value,
                "favorite_category": c.favorite_category,
            }
            for c in customer_models[:50]
        ],
    }

    # Save to local data/latest_simulation.json
    snapshot_storage_service.save_local_snapshot(result)

    return result
