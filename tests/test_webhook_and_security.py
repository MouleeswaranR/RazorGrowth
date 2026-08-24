import hmac
import hashlib
from app.integrations.razorpay_webhook_handler import RazorpayWebhookHandler


def test_webhook_signature_verification_valid():
    """Verifies that matching HMAC SHA256 signature is accepted."""
    handler = RazorpayWebhookHandler()
    handler._webhook_secret = "test_secret_key_123"

    payload_body = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_123","amount":100000,"status":"captured","method":"upi"}}}}'
    valid_signature = hmac.new(
        key=b"test_secret_key_123",
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    assert handler.verify_signature(payload_body, valid_signature) is True


def test_webhook_signature_verification_invalid():
    """Verifies that mismatched signature is rejected."""
    handler = RazorpayWebhookHandler()
    handler._webhook_secret = "test_secret_key_123"

    payload_body = b'{"event":"payment.captured"}'
    fake_signature = "bad_signature_value_xyz"

    assert handler.verify_signature(payload_body, fake_signature) is False


def test_webhook_payload_extraction():
    """Verifies that payment details are accurately extracted from JSON webhook payload."""
    handler = RazorpayWebhookHandler()
    sample_event = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_456",
                    "order_id": "order_test_789",
                    "amount": 299900,  # 2999.00 in paise
                    "status": "captured",
                    "method": "upi",
                }
            }
        }
    }

    extracted = handler.extract_event_payload(sample_event)
    assert extracted["event"] == "payment.captured"
    assert extracted["payment_id"] == "pay_test_456"
    assert extracted["amount"] == 2999.00
    assert extracted["method"] == "upi"
