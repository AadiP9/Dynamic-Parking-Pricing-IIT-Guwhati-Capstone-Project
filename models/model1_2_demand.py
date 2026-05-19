from config import BASE_PRICE, MIN_PRICE, MAX_PRICE, MODEL2_PARAMS


def demand_based_price(
    occupancy: int,
    capacity: int,
    queue_length: int,
    traffic: float,
    is_special_day: bool,
    vehicle_weight: float,
) -> float:
    """
    Model 2 — Demand-based pricing.
    Combines occupancy ratio, queue, traffic, special events, and vehicle type.
    """
    if capacity == 0:
        return BASE_PRICE

    p = MODEL2_PARAMS
    occupancy_ratio = occupancy / capacity

    demand_score = (
        p['alpha'] * occupancy_ratio
        + p['beta'] * min(queue_length / 10.0, 1.0)
        + p['gamma'] * min(traffic / 100.0, 1.0)
        + p['delta'] * float(is_special_day)
        + p['epsilon'] * (vehicle_weight - 1.0)
    )

    # Normalise to [-1, 1] range then scale
    demand_score = max(-1.0, min(1.0, demand_score - p['lambda_']))

    new_price = BASE_PRICE * (1 + demand_score)
    return float(max(MIN_PRICE, min(MAX_PRICE, new_price)))
