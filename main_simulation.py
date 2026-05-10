import os
import random
import threading

import numpy as np
import pandas as pd
import pathway as pw
import panel as pn
import bokeh.plotting

from bokeh.models import ColumnDataSource, HoverTool

from models.model1_1_baseline import baseline_price
from models.model1_2_demand import demand_based_price
from models.model_3_competitive import competitive_price

from utils.helpers import preprocess_data, create_lot_info
from utils.geospatial import calculate_distances, get_nearby_lots

from config import *

# ---------------------------------------------------
# NUMPY VERSION CHECK
# ---------------------------------------------------

assert np.__version__.startswith("1.")

# ---------------------------------------------------
# PANEL INITIALIZATION
# ---------------------------------------------------

pn.extension()

# ---------------------------------------------------
# LOAD DATASET
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(BASE_DIR, "data", "parking_stream.csv")

raw_df = pd.read_csv(csv_path)

processed_df = preprocess_data(raw_df)

lot_info = create_lot_info(processed_df)

indices, distances = calculate_distances(
    processed_df[["ParkingLotID", "Latitude", "Longitude"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

# ---------------------------------------------------
# PATHWAY SCHEMA
# ---------------------------------------------------

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

# ---------------------------------------------------
# STREAMING DATA
# ---------------------------------------------------

data = pw.demo.replay_csv(
    csv_path,
    schema=ParkingSchema,
    input_rate=500
)

data = data.with_columns(
    t=data.Timestamp.dt.strptime("%Y-%m-%d %H:%M:%S"),
    lot_id=data.ParkingLotID
)

# ---------------------------------------------------
# PRICING STATE
# ---------------------------------------------------

class PricingState(pw.Schema):
    lot_id: str
    last_price: float
    model: int

# ---------------------------------------------------
# PRICE UPDATE LOGIC
# ---------------------------------------------------

def update_prices(state, row):

    last_price = (
        state.last_price
        if state.last_price is not None
        else BASE_PRICE
    )

    model = (
        state.model
        if state.model is not None
        else 2
    )

    # ---------------- MODEL 1 ----------------

    if model == 1:

        price = baseline_price(
            last_price,
            row.Occupancy,
            row.Capacity
        )

    # ---------------- MODEL 2 ----------------

    elif model == 2:

        price = demand_based_price(
            row.Occupancy,
            row.Capacity,
            row.QueueLength,
            row.Traffic,
            row.IsSpecialDay,
            row.VehicleWeight
        )

    # ---------------- MODEL 3 ----------------

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

# ---------------------------------------------------
# INITIAL GRAPH DATA
# ---------------------------------------------------

initial_time = pd.Timestamp.now()

source = ColumnDataSource({

    "t": [
        initial_time - pd.Timedelta(seconds=1),
        initial_time
    ],

    "price": [
        30.0,
        32.0
    ],

    "lot": [
        "Lot A",
        "Lot A"
    ],

    "occupancy": [
        70,
        75
    ],

    "capacity": [
        100,
        100
    ]
})

# ---------------------------------------------------
# DESCRIPTION PANEL
# ---------------------------------------------------

description = pn.pane.Markdown("""

# Dynamic Parking Pricing Dashboard

This simulation demonstrates how parking prices dynamically change in real-time based on:

- Parking occupancy
- Queue length
- Traffic conditions
- Vehicle type
- Special event days
- Nearby competitor parking prices

## How It Works

The system continuously analyzes parking demand and adjusts prices dynamically:

- Higher demand → Higher parking prices
- Lower demand → Lower parking prices
- Nearby parking lots influence competitive pricing

## Pricing Models Used

### Model 1 — Baseline Pricing
Simple occupancy-based pricing adjustment.

### Model 2 — Demand-Based Pricing
Uses:
- Occupancy
- Queue length
- Traffic conditions
- Vehicle type
- Special events

### Model 3 — Competitive Pricing
Adds geospatial competitor analysis to optimize prices.

""")

# ---------------------------------------------------
# CREATE BOKEH PLOT
# ---------------------------------------------------

plot = bokeh.plotting.figure(

    height=450,
    width=900,

    sizing_mode="stretch_width",

    x_axis_type="datetime",

    title="Real-Time Dynamic Parking Prices"
)

plot.line(

    "t",
    "price",

    source=source,

    line_width=3,

    color="blue",

    legend_label="Parking Price"
)

plot.circle(

    "t",
    "price",

    source=source,

    size=8,

    color="red"
)

plot.add_tools(

    HoverTool(

        tooltips=[

            ("Lot", "@lot"),

            ("Price", "$@price"),

            ("Occupancy", "@occupancy/@capacity"),

            ("Time", "@t{%F %T}")

        ],

        formatters={
            "@t": "datetime"
        }
    )
)

plot.legend.location = "top_left"

# ---------------------------------------------------
# SIMULATED REAL-TIME STREAMING
# ---------------------------------------------------

def update_data():

    new_data = {

        "t": [pd.Timestamp.now()],

        "price": [random.randint(10, 50)],

        "lot": ["Lot A"],

        "occupancy": [random.randint(50, 100)],

        "capacity": [100]
    }

    source.stream(
        new_data,
        rollover=100
    )

# Update every second

pn.state.add_periodic_callback(
    update_data,
    period=1000
)

# ---------------------------------------------------
# DASHBOARD TEMPLATE
# ---------------------------------------------------

template = pn.template.FastListTemplate(

    title="IIT Guwahati Capstone Project — Dynamic Parking Pricing",

    main=[
        description,
        plot
    ],

    accent_base_color="#0072B5",

    header_background="#0072B5"
)

# ---------------------------------------------------
# PATHWAY PIPELINE
# ---------------------------------------------------

def run_pipeline():

    pw.run(
        monitoring_level=pw.MonitoringLevel.NONE
    )

# ---------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------

if __name__ == "__main__":

    # Start Pathway in background

    threading.Thread(

        target=run_pipeline,

        daemon=True

    ).start()

    # Start Panel server

    pn.serve(

        template,

        address="0.0.0.0",

        port=int(os.environ.get("PORT", 5006)),

        show=False,

        websocket_origin=["*"]
    )
