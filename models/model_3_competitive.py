from config import BASE_PRICE, MIN_PRICE, MAX_PRICE


def competitive_price(
    lot_id: str,
    last_price: float,
    occupancy: int,
    capacity: int,
    competitor_prices: list,
) -> float:
    """
    Model 3 — Competitive pricing.
    Adjusts price relative to nearby competitor average and own occupancy.
    """
    if capacity == 0:
        return last_price

    occupancy_ratio = occupancy / capacity

    if competitor_prices:
        avg_competitor = sum(competitor_prices) / len(competitor_prices)
    else:
        avg_competitor = BASE_PRICE

    # If we're busier than half capacity, price toward competitor avg or above
    if occupancy_ratio > 0.5:
        target = avg_competitor * (1 + 0.1 * (occupancy_ratio - 0.5))
    else:
        target = avg_competitor * (1 - 0.1 * (0.5 - occupancy_ratio))

    # Smooth transition: move 20% toward target each tick
    new_price = last_price + 0.2 * (target - last_price)
    return float(max(MIN_PRICE, min(MAX_PRICE, new_price)))
