import uuid
import random
from datetime import datetime
from app.models.order import OrderModel


def simulate_campaign_conversions(
    treatment_customers: list[dict],
    control_customers: list[dict],
    merchant_id: str,
    product_ids: list[str] | None = None,
    baseline_conversion_rate: float = 0.045,
    campaign_uplift_multiplier: float = 2.8,
    average_order_value: float = 2850.0,
) -> dict:
    """Generates historical baseline order data for treatment/control cohorts using independent random draws.

    NOTE: This function is used only for historical simulation data (the 500-customer
    pre-launch dataset). It does NOT model live experiment results — those are measured
    from real Razorpay webhook events via the experiment_assignments table. Each customer
    independently converts with the given rate; no post-hoc adjustment is made.
    """
    valid_product_ids = product_ids or []
    treatment_rate = min(0.35, baseline_conversion_rate * campaign_uplift_multiplier)

    treatment_orders = _draw_cohort_conversions(
        treatment_customers, merchant_id, valid_product_ids, treatment_rate, average_order_value,
    )
    control_orders = _draw_cohort_conversions(
        control_customers, merchant_id, valid_product_ids, baseline_conversion_rate, average_order_value,
    )

    return {
        "treatment_total": len(treatment_customers),
        "treatment_conversions": len(treatment_orders),
        "control_total": len(control_customers),
        "control_conversions": len(control_orders),
        "treatment_orders": treatment_orders,
        "control_orders": control_orders,
        "total_revenue": sum(o.amount for o in treatment_orders + control_orders),
    }


def _draw_cohort_conversions(
    customers: list[dict],
    merchant_id: str,
    product_ids: list[str],
    conversion_rate: float,
    average_order_value: float,
) -> list[OrderModel]:
    """Creates historical order records for each customer who independently converts at the given rate."""
    converted_orders: list[OrderModel] = []
    now = datetime.utcnow()

    for customer_info in customers:
        if random.random() < conversion_rate:
            order_value = average_order_value * random.uniform(0.8, 1.45)
            selected_product_id = random.choice(product_ids) if product_ids else f"prod_{merchant_id[:8]}"
            converted_orders.append(OrderModel(
                id=f"order_{uuid.uuid4().hex[:12]}",
                merchant_id=merchant_id,
                customer_id=customer_info["customer_id"],
                product_id=selected_product_id,
                quantity=1,
                amount=round(order_value, 2),
                status="completed",
                created_at=now,
            ))

    return converted_orders


