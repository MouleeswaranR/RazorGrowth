import uuid
import random
from app.models.order import OrderModel
from app.models.payment import PaymentModel

PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet"]
METHOD_SUCCESS_RATES = {
    "upi": 0.95,
    "card": 0.84,
    "netbanking": 0.90,
    "wallet": 0.92,
}


def generate_synthetic_payments_batch(orders: list[OrderModel]) -> list[PaymentModel]:
    """Simulates payment attempts with realistic channel success and failure distributions."""
    payments: list[PaymentModel] = []

    for order in orders:
        payment_id = f"pay_{uuid.uuid4().hex[:14]}"
        chosen_method = random.choices(
            PAYMENT_METHODS,
            weights=[0.60, 0.25, 0.10, 0.05],
        )[0]
        success_rate = METHOD_SUCCESS_RATES[chosen_method]
        is_successful = random.random() < success_rate

        status = "captured" if is_successful else "failed"
        error_reason = None if is_successful else "PAYMENT_GATEWAY_TIMEOUT"

        payments.append(
            PaymentModel(
                id=payment_id,
                order_id=order.id,
                payment_method=chosen_method,
                amount=order.amount,
                status=status,
                error_reason=error_reason,
                created_at=order.created_at,
            )
        )
    return payments
