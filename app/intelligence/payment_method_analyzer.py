from collections import Counter
from app.models.payment import PaymentModel


def analyze_payment_method_performance(
    payments: list[PaymentModel],
) -> dict[str, dict]:
    """Computes success rates and estimated lost GMV per payment method."""
    method_stats: dict[str, dict] = {}

    payments_by_method: dict[str, list[PaymentModel]] = {}
    for payment in payments:
        payments_by_method.setdefault(payment.payment_method, []).append(payment)

    for method, method_payments in payments_by_method.items():
        total = len(method_payments)
        successful = sum(1 for p in method_payments if p.status == "captured")
        failed = total - successful
        success_rate = successful / max(1, total)
        failed_gmv = sum(p.amount for p in method_payments if p.status == "failed")

        method_stats[method] = {
            "total_transactions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 4),
            "estimated_lost_gmv": round(failed_gmv, 2),
        }

    return method_stats


def find_underperforming_payment_methods(
    method_stats: dict[str, dict],
    benchmark_rate: float = 0.92,
) -> list[dict]:
    """Identifies payment methods performing below the benchmark success rate threshold."""
    underperformers = []
    for method, stats in method_stats.items():
        if stats["success_rate"] < benchmark_rate and stats["total_transactions"] >= 20:
            gap = benchmark_rate - stats["success_rate"]
            recoverable_gmv = stats["estimated_lost_gmv"] * 0.60
            underperformers.append({
                "method": method,
                "current_rate": stats["success_rate"],
                "benchmark_rate": benchmark_rate,
                "gap_percentage": round(gap * 100, 2),
                "estimated_lost_gmv": stats["estimated_lost_gmv"],
                "recoverable_gmv": round(recoverable_gmv, 2),
            })

    return sorted(underperformers, key=lambda x: x["estimated_lost_gmv"], reverse=True)
