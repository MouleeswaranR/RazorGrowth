from collections import Counter
from app.models.customer import CustomerModel
from app.models.order import OrderModel, PAID_ORDER_STATUSES
from app.models.payment import PaymentModel
from app.models.product import ProductModel


class ContextEngine:
    """Aggregates and filters raw store transactions into high-signal analytical context."""

    def build_merchant_growth_context(
        self,
        merchant_id: str,
        customers: list[CustomerModel],
        orders: list[OrderModel],
        payments: list[PaymentModel],
        products: list[ProductModel],
    ) -> dict:
        """Constructs an integrated merchant snapshot for agent reasoning."""
        total_customers = len(customers)
        # Count only orders where money was actually received; unpaid "pending_checkout"
        # A/B cohort orders would otherwise inflate revenue and dilute AOV.
        paid_orders = [o for o in orders if o.status in PAID_ORDER_STATUSES]
        total_revenue = sum(o.amount for o in paid_orders)
        aov = total_revenue / max(1, len(paid_orders))

        segments: Counter = Counter(c.customer_segment for c in customers)
        dormant_vips = sum(1 for c in customers if c.customer_segment in ("VIP Dormant", "Loyal At Risk"))

        successful_payments = sum(1 for p in payments if p.status == "captured")
        payment_success_rate = successful_payments / max(1, len(payments))

        # Retrieve relevant episodic memories from vector memory
        from app.services.vector_memory_service import vector_memory_service
        past_memories = vector_memory_service.find_similar_memories(
            merchant_id=merchant_id,
            query_text=f"Growth opportunities for {merchant_id} dormant VIP recovery and payment optimization",
            top_k=2,
        )

        return {
            "merchant_id": merchant_id,
            "total_customers": total_customers,
            "total_revenue_inr": round(total_revenue, 2),
            "average_order_value_inr": round(aov, 2),
            "segment_breakdown": dict(segments),
            "dormant_vip_count": dormant_vips,
            "payment_overall_success_rate": round(payment_success_rate, 4),
            "catalog_size": len(products),
            "retrieved_memory": past_memories,
        }

context_engine = ContextEngine()
