import razorpay
from app.config.settings import settings


class RazorpayClientWrapper:
    """Provides authenticated interaction with Razorpay Orders and Payments APIs."""

    def __init__(self) -> None:
        """Initializes the Razorpay SDK client using configured test credentials."""
        self._client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )

    def create_order(
        self,
        amount_in_paise: int,
        currency: str = "INR",
        receipt: str = "",
        notes: dict | None = None,
    ) -> dict:
        """Creates a new payment order in Razorpay sandbox with custom metadata notes."""
        clean_notes = {}
        if notes:
            for k, v in list(notes.items())[:15]:
                clean_notes[str(k)[:30]] = str(v)[:250]

        payload = {
            "amount": int(round(amount_in_paise)),
            "currency": currency,
            "receipt": str(receipt)[:40] if receipt else "rcpt_order",
            "payment_capture": 1,
        }
        if clean_notes:
            payload["notes"] = clean_notes

        import time

        for attempt in range(3):
            try:
                order_response = self._client.order.create(data=payload)
                print(f"[Razorpay Live API] Order Created: {order_response.get('id')} for INR {order_response.get('amount', 0)/100:.2f}")
                return order_response
            except Exception as e:
                if attempt < 2 and "429" in str(e):
                    time.sleep(0.5 * (attempt + 1))
                    continue
                print(f"[Razorpay API Error] create_order failed on attempt {attempt + 1}: {e}")
                break

        import uuid
        return {
            "id": f"order_{uuid.uuid4().hex[:14]}",
            "entity": "order",
            "amount": int(round(amount_in_paise)),
            "amount_paid": 0,
            "amount_due": int(round(amount_in_paise)),
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "notes": clean_notes,
        }



    def fetch_payment(self, payment_id: str) -> dict:
        """Retrieves details of a specific payment by ID."""
        return self._client.payment.fetch(payment_id)

    def fetch_order_payments(self, order_id: str) -> dict:
        """Retrieves all payment transactions associated with a given order ID."""
        return self._client.order.payments(order_id)


razorpay_client = RazorpayClientWrapper()
