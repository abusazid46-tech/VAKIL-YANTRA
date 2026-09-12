"""Razorpay integration placeholder."""


class PaymentGateway:
    provider = "razorpay"

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return bool(payload and signature)

