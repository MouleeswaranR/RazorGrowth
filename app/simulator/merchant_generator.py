import uuid
from app.models.merchant import MerchantModel


def generate_synthetic_merchant(merchant_name: str = "StyleKart") -> MerchantModel:
    """Creates and returns a synthetic merchant model with default retail attributes."""
    merchant_id = f"merch_{uuid.uuid4().hex[:12]}"
    return MerchantModel(
        id=merchant_id,
        name=merchant_name,
        category="E-commerce Fashion & Apparel",
        currency="INR",
    )
