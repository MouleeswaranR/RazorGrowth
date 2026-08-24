from collections import Counter
from app.models.customer import CustomerModel
from app.models.order import OrderModel
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
        total_revenue = sum(o.amount for o in orders if o.status == "completed")
        aov = total_revenue / max(1, len(orders))

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

    def extract_cohort_subcontext(
        self,
        customers: list[CustomerModel],
        target_segment: str,
    ) -> dict:
        """Extracts targeted statistical metrics for a specific customer cohort."""
        cohort = [c for c in customers if c.customer_segment == target_segment]
        if not cohort:
            return {"cohort_size": 0, "average_spend": 0.0}

        avg_spend = sum(c.total_spend_amount for c in cohort) / len(cohort)
        return {
            "target_segment": target_segment,
            "cohort_size": len(cohort),
            "average_spend_inr": round(avg_spend, 2),
            "top_locations": Counter(c.location for c in cohort if c.location).most_common(3),
        }


context_engine = ContextEngine()
