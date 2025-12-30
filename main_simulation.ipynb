# =====================================================
# ENVIRONMENT SETUP (CRITICAL)
# CELL 1
# =====================================================
import sys
import subprocess

print("Installing compatible libraries...")

subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "numpy<2.0",
    "pathway",
    "pandas",
    "bokeh",
    "panel",
    "scikit-learn",
    "--upgrade"
])

print("Installation complete.")
print("⚠️ PLEASE RESTART THE RUNTIME/KERNEL NOW.")


# CELL 2
import numpy as np
import pandas as pd
import pathway as pw

import os
import time
import threading
from datetime import datetime, timedelta

import bokeh.plotting
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20
import panel as pn

print("NumPy version:", np.__version__)
assert np.__version__.startswith("1."), "NumPy 2.x detected — environment is broken"


# CELL 3
from models.model1_baseline import baseline_price
from models.model2_demand import demand_based_price
from models.model3_competitive import competitive_price

from utils.helpers import preprocess_data, create_lot_info
from utils.geospatial import calculate_distances, get_nearby_lots

from config import *


# CELL 4
os.makedirs("data", exist_ok=True)
data_path = "data/dataset.csv"

if not os.path.exists(data_path):
    print("Dataset not found. Creating dummy data...")
    dates = pd.date_range("2024-01-01", periods=200, freq="5min")

    df_dummy = pd.DataFrame({
        "LastUpdatedDate": dates.strftime("%d-%m-%Y"),
        "LastUpdatedTime": dates.strftime("%H:%M:%S"),
        "Occupancy": np.random.randint(10, 90, len(dates)),
        "Capacity": 100,
        "QueueLength": np.random.randint(0, 15, len(dates)),
        "Traffic": np.random.rand(len(dates)),
        "IsSpecialDay": False,
        "VehicleType": "car",
        "Latitude": 12.9716,
        "Longitude": 77.5946,
        "ParkingLotID": "P1"
    })

    df_dummy.to_csv(data_path, index=False)

df = preprocess_data(pd.read_csv(data_path))
lot_info = create_lot_info(df)

unique_lots = df[["ParkingLotID", "Latitude", "Longitude"]].drop_duplicates()
distances, indices = calculate_distances(unique_lots)

df.to_csv("data/parking_stream.csv", index=False)


# CELL 5
class ParkingSchema(pw.Schema):
    Timestamp: str
    ParkingLotID: str
    Occupancy: int
    Capacity: int
    QueueLength: int
    Traffic: float
    IsSpecialDay: bool
    VehicleWeight: float
    Latitude: float
    Longitude: float


data = pw.demo.replay_csv(
    "data/parking_stream.csv",
    schema=ParkingSchema,
    input_rate=500
)

data = data.with_columns(
    t=data.Timestamp.dt.strptime("%Y-%m-%d %H:%M:%S"),
    lot_id=data.ParkingLotID
)


# =====================================================
# CELL 6 — STATEFUL PRICING LOGIC (PATHWAY-CORRECT)
# =====================================================

# ---- 1. STATE SCHEMA (NO DEFAULTS) ----
class PricingState(pw.Schema):
    lot_id: str
    last_price: float
    model: int


# ---- 2. REDUCER FUNCTION (PURE + FUNCTIONAL) ----
def update_prices(state, row):
    # ---- Initialize state ----
    last_price = state.last_price if state.last_price is not None else BASE_PRICE
    model = state.model if state.model is not None else 2  # demand-based default

    # ---- Pricing logic ----
    if model == 1:
        price = baseline_price(
            last_price,
            row.Occupancy,
            row.Capacity
        )

    elif model == 2:
        price = demand_based_price(
            row.Occupancy,
            row.Capacity,
            row.QueueLength,
            row.Traffic,
            row.IsSpecialDay,
            row.VehicleWeight
        )

    else:
        nearby_lots = get_nearby_lots(
            row.ParkingLotID,
            lot_info,
            distances,
            indices,
            MAX_DISTANCE_KM
        )

        competitor_prices = [BASE_PRICE] * len(nearby_lots)

        price = competitive_price(
            row.ParkingLotID,
            last_price,
            row.Occupancy,
            row.Capacity,
            competitor_prices
        )

    return {
        "lot_id": row.lot_id,
        "last_price": price,
        "model": model,
    }


# CELL 7
pn.extension()

source = ColumnDataSource({
    "t": [],
    "price": [],
    "lot": [],
    "occupancy": [],
    "capacity": [],
})

plot = bokeh.plotting.figure(
    height=400,
    width=800,
    x_axis_type="datetime",
    title="Real-Time Parking Price"
)

plot.line("t", "price", source=source, line_width=2)

plot.add_tools(HoverTool(
    tooltips=[
        ("Lot", "@lot"),
        ("Price", "@price"),
        ("Occupancy", "@occupancy/@capacity")
    ]
))

dashboard = pn.Column(plot)
dashboard


# CELL 8
def run_pipeline():
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)

threading.Thread(target=run_pipeline, daemon=True).start()
