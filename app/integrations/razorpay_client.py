import time
import uuid
import razorpay
from app.config.settings import settings


class RazorpayClientWrapper:
    """Provides authenticated interaction with Razorpay Orders, Payments, and Refunds APIs with exponential backoff retry."""

    def __init__(self) -> None:
        """Initializes the Razorpay SDK client using configured test credentials."""
        self._client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )

    def _retry_with_backoff(self, operation_name: str, api_call: callable, max_retries: int = 3) -> dict:
        """Executes Razorpay API call with exponential backoff retry logic."""
        for attempt in range(max_retries):
            try:
                result = api_call()
                if isinstance(result, dict):
                    result.setdefault("is_mock", False)
                return result
            except Exception as e:
                error_str = str(e)
                is_retryable = any(code in error_str for code in ["429", "503", "502", "timeout"])
                
                if attempt < max_retries - 1 and is_retryable:
                    backoff_seconds = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                    print(f"[Razorpay Retry] {operation_name} failed (attempt {attempt + 1}), retrying in {backoff_seconds}s: {e}")
                    time.sleep(backoff_seconds)
                    continue
                
                print(f"[Razorpay API Error] {operation_name} failed after {attempt + 1} attempts: {e}")
                raise

    def create_order(
        self,
        amount_in_paise: int,
        currency: str = "INR",
        receipt: str = "",
        notes: dict | None = None,
    ) -> dict:
        """Creates a new payment order in Razorpay sandbox with custom metadata notes and retry logic."""
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

        try:
            order_response = self._retry_with_backoff(
                "create_order",
                lambda: self._client.order.create(data=payload)
            )
            print(f"[Razorpay Live API] Order Created: {order_response.get('id')} for INR {order_response.get('amount', 0)/100:.2f}")
            return order_response
        except Exception:
            # Offline fallback for demo resilience
            print("[Razorpay FALLBACK] Returning MOCK order — no live Razorpay order was created.")
            return {
                "id": f"order_mock_{uuid.uuid4().hex[:12]}",
                "entity": "order",
                "amount": int(round(amount_in_paise)),
                "amount_paid": 0,
                "amount_due": int(round(amount_in_paise)),
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "notes": clean_notes,
                "is_mock": True,
            }

    def create_refund(
        self,
        payment_id: str,
        amount_in_paise: int | None = None,
        notes: dict | None = None,
        speed: str = "normal"
    ) -> dict:
        """Creates a refund for a captured payment with retry logic."""
        clean_notes = {}
        if notes:
            for k, v in list(notes.items())[:10]:
                clean_notes[str(k)[:30]] = str(v)[:250]

        payload = {"speed": speed}
        if amount_in_paise:
            payload["amount"] = int(round(amount_in_paise))
        if clean_notes:
            payload["notes"] = clean_notes

        try:
            refund_response = self._retry_with_backoff(
                "create_refund",
                lambda: self._client.payment.refund(payment_id, payload)
            )
            print(f"[Razorpay Refund] Created: {refund_response.get('id')} for payment {payment_id}")
            return refund_response
        except Exception as e:
            # Return error indicator for caller to handle
            print(f"[Razorpay Refund Error] Failed for payment {payment_id}: {e}")
            return {
                "id": f"rfnd_mock_{uuid.uuid4().hex[:12]}",
                "entity": "refund",
                "payment_id": payment_id,
                "amount": amount_in_paise or 0,
                "status": "failed",
                "error": str(e),
                "is_mock": True,
            }

    def fetch_payment(self, payment_id: str) -> dict:
        """Fetches payment details with retry logic."""
        try:
            payment = self._retry_with_backoff(
                "fetch_payment",
                lambda: self._client.payment.fetch(payment_id)
            )
            return payment
        except Exception as e:
            print(f"[Razorpay Fetch Error] Payment {payment_id}: {e}")
            return {"error": str(e), "is_mock": True}

    def create_payment_link(
        self,
        amount_in_paise: int,
        currency: str = "INR",
        description: str = "",
        customer_name: str = "",
        customer_email: str = "",
        customer_contact: str = "",
        notes: dict | None = None,
        callback_url: str = "",
        callback_method: str = "get",
    ) -> dict:
        """Creates a payment link for programmatic checkout with retry logic."""
        clean_notes = {}
        if notes:
            for k, v in list(notes.items())[:10]:
                clean_notes[str(k)[:30]] = str(v)[:250]

        payload = {
            "amount": int(round(amount_in_paise)),
            "currency": currency,
            "description": str(description)[:250] if description else "Checkout Payment",
            "customer": {
                "name": str(customer_name)[:50] if customer_name else "",
                "email": str(customer_email)[:50] if customer_email else "",
                "contact": str(customer_contact)[:15] if customer_contact else "",
            },
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
            payload["callback_method"] = callback_method
        
        if clean_notes:
            payload["notes"] = clean_notes

        try:
            link_response = self._retry_with_backoff(
                "create_payment_link",
                lambda: self._client.invoice.create(data=payload)
            )
            print(f"[Razorpay Payment Link] Created: {link_response.get('short_url')} for INR {amount_in_paise/100:.2f}")
            return link_response
        except Exception as e:
            print(f"[Razorpay Payment Link Error] Failed: {e}")
            return {
                "id": f"plink_mock_{uuid.uuid4().hex[:12]}",
                "entity": "invoice",
                "amount": int(round(amount_in_paise)),
                "currency": currency,
                "status": "failed",
                "short_url": f"https://rzp.io/l/mock_{uuid.uuid4().hex[:8]}",
                "error": str(e),
                "is_mock": True,
            }



razorpay_client = RazorpayClientWrapper()
