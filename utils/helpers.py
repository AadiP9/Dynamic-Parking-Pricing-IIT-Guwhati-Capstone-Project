import pandas as pd


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and type-cast the raw parking dataframe."""
    df = df.copy()

    # Ensure correct types
    df["Occupancy"] = pd.to_numeric(df["Occupancy"], errors="coerce").fillna(0).astype(int)
    df["Capacity"] = pd.to_numeric(df["Capacity"], errors="coerce").fillna(100).astype(int)
    df["QueueLength"] = pd.to_numeric(df["QueueLength"], errors="coerce").fillna(0).astype(int)
    df["Traffic"] = pd.to_numeric(df["Traffic"], errors="coerce").fillna(0.0).astype(float)
    df["IsSpecialDay"] = df["IsSpecialDay"].astype(bool)
    df["VehicleWeight"] = pd.to_numeric(df["VehicleWeight"], errors="coerce").fillna(1.0).astype(float)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce").fillna(26.1)
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce").fillna(91.7)

    return df


def create_lot_info(df: pd.DataFrame) -> dict:
    """Return a dict of lot_id -> {lat, lon, capacity} from unique lots."""
    lot_info = {}
    unique = df[["ParkingLotID", "Latitude", "Longitude", "Capacity"]].drop_duplicates("ParkingLotID")
    for _, row in unique.iterrows():
        lot_info[row["ParkingLotID"]] = {
            "lat": row["Latitude"],
            "lon": row["Longitude"],
            "capacity": row["Capacity"],
        }
    return lot_info
