from collections import Counter, defaultdict
from app.models.order import OrderModel


def build_category_copurchase_matrix(
    orders: list[OrderModel],
    product_category_map: dict[str, str],
) -> dict[str, list[tuple[str, float]]]:
    """Builds a co-purchase frequency matrix identifying which categories are bought together."""
    customer_categories: dict[str, set[str]] = defaultdict(set)

    for order in orders:
        category = product_category_map.get(order.product_id)
        if category:
            customer_categories[order.customer_id].add(category)

    pair_counts: Counter = Counter()
    category_totals: Counter = Counter()

    for categories in customer_categories.values():
        for cat in categories:
            category_totals[cat] += 1
        category_list = sorted(categories)
        for i, cat_a in enumerate(category_list):
            for cat_b in category_list[i + 1 :]:
                pair_counts[(cat_a, cat_b)] += 1

    affinity_map: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (cat_a, cat_b), co_count in pair_counts.most_common():
        confidence_a_to_b = co_count / max(1, category_totals[cat_a])
        confidence_b_to_a = co_count / max(1, category_totals[cat_b])

        affinity_map[cat_a].append((cat_b, round(confidence_a_to_b, 3)))
        affinity_map[cat_b].append((cat_a, round(confidence_b_to_a, 3)))

    for category in affinity_map:
        affinity_map[category].sort(key=lambda x: x[1], reverse=True)

    return dict(affinity_map)


def find_cross_sell_candidates(
    orders: list[OrderModel],
    product_category_map: dict[str, str],
    source_category: str,
    target_category: str,
) -> list[str]:
    """Finds customer IDs who bought source_category but never bought target_category."""
    customer_categories: dict[str, set[str]] = defaultdict(set)
    for order in orders:
        category = product_category_map.get(order.product_id)
        if category:
            customer_categories[order.customer_id].add(category)

    return [
        cid for cid, cats in customer_categories.items()
        if source_category in cats and target_category not in cats
    ]
