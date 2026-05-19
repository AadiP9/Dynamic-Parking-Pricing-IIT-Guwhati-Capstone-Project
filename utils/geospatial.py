import math
import numpy as np
import pandas as pd
from config import EARTH_RADIUS_KM, NEARBY_LOTS_K


def haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    r = EARTH_RADIUS_KM
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def calculate_distances(lots_df: pd.DataFrame):
    """
    Given a DataFrame with columns [ParkingLotID, Latitude, Longitude],
    return (indices_array, distances_matrix) where distances_matrix[i][j]
    is the km distance between lot i and lot j.
    """
    n = len(lots_df)
    indices = lots_df["ParkingLotID"].tolist()
    distances = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i != j:
                distances[i][j] = haversine(
                    lots_df.iloc[i]["Latitude"],
                    lots_df.iloc[i]["Longitude"],
                    lots_df.iloc[j]["Latitude"],
                    lots_df.iloc[j]["Longitude"],
                )
    return indices, distances


def get_nearby_lots(lot_id, lot_info: dict, distances, indices, max_distance_km: float):
    """
    Return a list of lot_ids that are within max_distance_km of the given lot_id.
    """
    if lot_id not in indices:
        return []

    i = indices.index(lot_id)
    nearby = []
    for j, other_id in enumerate(indices):
        if other_id != lot_id and distances[i][j] <= max_distance_km:
            nearby.append(other_id)
    return nearby[:NEARBY_LOTS_K]
