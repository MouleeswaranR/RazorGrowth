import hmac
import hashlib
from app.config.settings import settings


class RazorpayWebhookHandler:
    """Verifies cryptographic signatures and extracts event details from Razorpay webhooks."""

    def __init__(self) -> None:
        """Sets webhook secret token from settings."""
        self._webhook_secret = settings.razorpay_webhook_secret

    def verify_signature(self, raw_body: bytes, received_signature: str) -> bool:
        """Validates that incoming webhook payload matches the expected HMAC SHA256 signature."""
        if not self._webhook_secret:
            return True
        expected_signature = hmac.new(
            key=self._webhook_secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_signature, received_signature)

    def extract_event_payload(self, event_data: dict) -> dict:
        """Parses event name, notes, and entity metadata from Razorpay webhook payload."""
        event_name = event_data.get("event", "unknown")
        payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
        order_entity = event_data.get("payload", {}).get("order", {}).get("entity", {})
        notes = payment_entity.get("notes") or order_entity.get("notes") or {}
        return {
            "event": event_name,
            "payment_id": payment_entity.get("id"),
            "order_id": payment_entity.get("order_id") or order_entity.get("id"),
            "amount": (payment_entity.get("amount") or order_entity.get("amount") or 0) / 100.0,
            "status": payment_entity.get("status") or order_entity.get("status"),
            "method": payment_entity.get("method", "upi"),
            "email": payment_entity.get("email"),
            "contact": payment_entity.get("contact"),
            "notes": notes,
            "campaign_id": notes.get("campaign_id"),
            "customer_id": notes.get("customer_id"),
            "variant": notes.get("variant", "treatment"),
            "session_id": notes.get("session_id"),
            "error_code": payment_entity.get("error_code"),
            "error_description": payment_entity.get("error_description"),
        }



razorpay_webhook_handler = RazorpayWebhookHandler()
