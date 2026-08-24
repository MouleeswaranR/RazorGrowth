class MessageSimulator:
    """Simulates delivery of marketing communications across email and messaging channels."""

    def __init__(self) -> None:
        """Initializes sent message history store."""
        self._sent_messages: list[dict] = []

    def dispatch_email(self, recipient_email: str, subject: str, body: str) -> dict:
        """Simulates sending an email notification and records delivery log."""
        record = {
            "channel": "email",
            "recipient": recipient_email,
            "subject": subject,
            "status": "delivered",
        }
        self._sent_messages.append(record)
        return record

message_simulator = MessageSimulator()
