# # ENVIRONMENT SETUP (CRITICAL)
# # CELL 1
# import sys
# import subprocess

# print("Installing compatible libraries...")

# subprocess.check_call([
#     sys.executable, "-m", "pip", "install",
#     "numpy<2.0",
#     "pathway",
#     "pandas",
#     "bokeh",
#     "panel",
#     "scikit-learn",
#     "--upgrade"
# ])

# print("Installation complete.")
# print("⚠️ PLEASE RESTART THE RUNTIME/KERNEL NOW.")

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
from models.model1_1_baseline import baseline_price
from models.model1_2_demand import demand_based_price
from models.model_3_competitive import competitive_price

from utils.helpers import preprocess_data, create_lot_info
from utils.geospatial import calculate_distances, get_nearby_lots

from config import *


# CELL 4
def preprocess_data(df):
    """
    Preprocess raw data for simulation

    Args:
        df (pd.DataFrame) : Raw input data

    Returns:
        pd.DataFrame : Preprocessed data
    """

    # Combine date and time
    df['Timestamp'] = pd.to_datetime(
        df['LastUpdatedDate'] + ' ' + df['LastUpdatedTime'],
        format="%d-%m-%Y %H:%M:%S"  # ← Fixed: changed %H-%M-%S to %H:%M:%S
    )

    column_mapping = {
        'Occupancy': 'Occupancy',
        'Capacity': 'Capacity',
        'QueueLength': 'QueueLength',
        'Traffic': 'Traffic',
        'IsSpecialDay': 'IsSpecialDay',
        'VehicleType': 'VehicleType',
        'Latitude': 'Latitude',
        'Longitude': 'Longitude',
        'ParkingLotID': 'ParkingLotID'
    }
    df = df.rename(columns=column_mapping)

    # Fill missing values
    df['QueueLength'] = df['QueueLength'].fillna(0)  # ← Fixed: changed fillna[0] to fillna(0)
    df['Traffic'] = df['Traffic'].fillna(1.0)
    df['IsSpecialDay'] = df['IsSpecialDay'].fillna(0).astype(bool)
    df['VehicleType'] = df['VehicleType'].fillna('car')

    # Add vehicle weight
    df['VehicleWeight'] = df['VehicleType'].map(VEHICLE_WEIGHTS).fillna(1.0)

    # Sort by timestamp
    return df.sort_values('Timestamp').reset_index(drop=True)


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


# CELL 6 — STATEFUL PRICING LOGIC (PATHWAY-CORRECT)
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
import panel as pn
import bokeh.plotting
from bokeh.models import ColumnDataSource, HoverTool
import pandas as pd
import random

pn.extension('ipywidgets')

# 1. Setup the empty data source
source = ColumnDataSource({
    "t": [],
    "price": [],
    "lot": [],
    "occupancy": [],
    "capacity": [],
})

# 2. Setup the plot
plot = bokeh.plotting.figure(
    height=400,
    width=800,
    x_axis_type="datetime",
    title="Real-Time Parking Price"
)

# Draw the line
plot.line("t", "price", source=source, line_width=2)

# Add hover tools
plot.add_tools(HoverTool(
    tooltips=[
        ("Lot", "@lot"),
        ("Price", "$@price"),
        ("Occupancy", "@occupancy/@capacity")
    ]
))

# 3. Create an update function to stream new data
def update_data():
    # In your real project, this data will come from your simulation loop or dataset.csv
    new_data = {
        "t": [pd.Timestamp.now()],
        "price": [random.randint(10, 50)], # Random price between $10 and $50
        "lot": ["Lot A"],
        "occupancy": [random.randint(50, 100)],
        "capacity": [100]
    }
    
    # .stream() pushes the new data to the chart. 
    # rollover=100 ensures the chart only keeps the latest 100 points so it doesn't crash.
    source.stream(new_data, rollover=100)

# 4. Trigger the update function every 1000 milliseconds (1 second)
callback = pn.state.add_periodic_callback(update_data, period=1000)

# 5. Display the dashboard
dashboard = pn.Column(plot)
dashboard.show()

# CELL 8
def run_pipeline():
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)

threading.Thread(target=run_pipeline, daemon=True).start()
