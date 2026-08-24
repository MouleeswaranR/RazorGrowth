import uuid


class DiscountCouponService:
    """Manages generation and validation of promotional coupon codes."""

    def __init__(self) -> None:
        """Initializes coupon repository."""
        self._active_coupons: dict[str, dict] = {}

    def issue_coupon(
        self,
        code: str,
        discount_type: str,
        discount_value: float,
        min_order_value: float = 0.0,
    ) -> dict:
        """Registers and returns a newly activated promotional discount coupon."""
        coupon_record = {
            "coupon_id": f"cpn_{uuid.uuid4().hex[:8]}",
            "code": code.upper(),
            "discount_type": discount_type,
            "discount_value": discount_value,
            "min_order_value": min_order_value,
            "is_active": True,
        }
        self._active_coupons[code.upper()] = coupon_record
        return coupon_record

    def validate_coupon(self, code: str) -> dict | None:
        """Checks if a coupon code is valid and active."""
        return self._active_coupons.get(code.upper())


discount_coupon_service = DiscountCouponService()
