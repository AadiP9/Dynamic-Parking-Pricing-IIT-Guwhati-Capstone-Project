from config import BASE_PRICE, MIN_PRICE, MAX_PRICE, ALPHA


def baseline_price(last_price: float, occupancy: int, capacity: int) -> float:
    """
    Model 1 — Baseline linear pricing.
    Adjusts price up/down by ALPHA * BASE_PRICE based on occupancy ratio.
    """
    if capacity == 0:
        return last_price

    occupancy_ratio = occupancy / capacity
    delta = ALPHA * BASE_PRICE * (occupancy_ratio - 0.5)
    new_price = last_price + delta
    return float(max(MIN_PRICE, min(MAX_PRICE, new_price)))
