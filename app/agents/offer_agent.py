from app.schemas.agent_outputs import OfferRecommendationOutput


class OfferAgent:
    """Selects margin-aware incentives and checkout interventions with explicit strategic rationale."""

    OFFER_STRATEGIES = {
        "payment_optimization": {
            "offer_code": "UPISWIFT",
            "discount_type": "flat",
            "discount_value": 50.0,
            "min_order": 299.0,
            "description": "1-Click UPI Smart Fallback & Checkout Nudge with ₹50 completion bonus",
            "urgency": "Complete checkout within 24 hours",
            "reasoning": "Payment drop-offs require friction removal rather than margin-eroding discounts. A ₹50 completion bonus incentivizes fast 1-click UPI checkout completion.",
        },
        "VIP Dormant": {
            "offer_code": "VIP15OFF",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "min_order": 1999.0,
            "description": "VIP Re-engagement: 15% off orders above ₹1,999",
            "urgency": "Expires in 7 days",
            "reasoning": "VIP reactivation justifies a 15% incentive backed by a ₹1,999 minimum order threshold to safeguard gross margin.",
        },
        "Loyal At Risk": {
            "offer_code": "COMEBACK10",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "min_order": 999.0,
            "description": "10% off loyalty comeback offer",
            "urgency": "Expires in 5 days",
            "reasoning": "A 10% loyalty comeback coupon re-establishes shopping cadence without excessive discounting.",
        },
        "Cross-Sell Cohort": {
            "offer_code": "BUNDLE15",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "min_order": 1499.0,
            "description": "15% off when adding recommended category companion item",
            "urgency": "Limited bundle availability",
            "reasoning": "Bundle discounts increase Average Order Value (AOV) by rewarding multi-item basket construction.",
        },
    }

    DEFAULT_OFFER = {
        "offer_code": "WELCOME10",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "min_order": 499.0,
        "description": "10% off on your next purchase",
        "urgency": "Valid for 7 days",
        "reasoning": "Standard baseline incentive to encourage conversion.",
    }

    def determine_optimal_offer(
        self,
        segment: str,
        average_spend: float = 2000.0,
    ) -> OfferRecommendationOutput:
        """Constructs a validated OfferRecommendationOutput schema tailored to opportunity and customer tier."""
        raw = self.OFFER_STRATEGIES.get(segment, self.DEFAULT_OFFER).copy()

        if segment == "VIP Dormant" and average_spend >= 8000:
            raw["discount_value"] = 20.0
            raw["offer_code"] = "VIP20OFF"
            raw["description"] = "Exclusive 20% off your next order above ₹1,999"
            raw["reasoning"] = "Top-tier VIP spend (>₹8,000) justifies maximum 20% re-acquisition discount."

        return OfferRecommendationOutput(
            offer_code=raw["offer_code"],
            discount_type=raw["discount_type"],
            discount_value=raw["discount_value"],
            min_order_value=raw["min_order"],
            description=raw["description"],
            urgency_text=raw["urgency"],
            reasoning=raw["reasoning"],
        )
