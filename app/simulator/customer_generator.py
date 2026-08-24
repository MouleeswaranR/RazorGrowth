import uuid
import random
from datetime import datetime, timedelta
from app.models.customer import CustomerModel

CITIES = [
    "Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune",
    "Chennai", "Kolkata", "Jaipur", "Ahmedabad", "Lucknow",
]
FIRST_NAMES = [
    "Aarav", "Priya", "Rahul", "Ananya", "Rohan", "Sneha",
    "Aditya", "Neha", "Vikram", "Pooja", "Karan", "Meera",
    "Arjun", "Divya", "Siddharth", "Kavya", "Nikhil", "Ishita",
]
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Mehta", "Iyer", "Nair",
    "Reddy", "Gupta", "Deshmukh", "Chopra", "Malhotra", "Joshi",
]

COHORT_DISTRIBUTION = {
    "vip_active": 0.10,
    "vip_dormant": 0.08,
    "loyal": 0.20,
    "new_recent": 0.15,
    "at_risk": 0.12,
    "one_time": 0.20,
    "standard": 0.15,
}


def _assign_cohort_label(index: int, total: int) -> str:
    """Assigns a behavioral cohort label based on position within the customer list."""
    position_ratio = index / total
    cumulative = 0.0
    for cohort_name, ratio in COHORT_DISTRIBUTION.items():
        cumulative += ratio
        if position_ratio < cumulative:
            return cohort_name
    return "standard"


def _compute_cohort_creation_date(cohort: str, base_time: datetime) -> datetime:
    """Determines customer creation date based on cohort behavioral timeline."""
    cohort_day_ranges = {
        "vip_active": (60, 85),
        "vip_dormant": (50, 80),
        "loyal": (30, 70),
        "new_recent": (1, 14),
        "at_risk": (40, 75),
        "one_time": (40, 80),
        "standard": (15, 60),
    }
    min_days, max_days = cohort_day_ranges.get(cohort, (15, 60))
    return base_time + timedelta(days=random.randint(min_days, max_days))


def generate_synthetic_customers_batch(
    merchant_id: str,
    count: int = 500,
) -> list[tuple[CustomerModel, str]]:
    """Generates customer profiles tagged with behavioral cohort labels for order distribution."""
    customers: list[tuple[CustomerModel, str]] = []
    base_time = datetime.utcnow() - timedelta(days=90)

    for index in range(count):
        customer_id = f"cust_{uuid.uuid4().hex[:12]}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}{index}@example.com"
        location = random.choice(CITIES)
        cohort = _assign_cohort_label(index, count)
        created_at = _compute_cohort_creation_date(cohort, base_time)

        customer = CustomerModel(
            id=customer_id,
            merchant_id=merchant_id,
            name=full_name,
            email=email,
            location=location,
            created_at=created_at,
        )
        customers.append((customer, cohort))

    return customers
