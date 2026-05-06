import os
import time
import random
import threading
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pathway as pw
import bokeh.plotting
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20
import panel as pn

assert np.__version__.startswith("1.")

from models.model1_1_baseline import baseline_price
from models.model1_2_demand import demand_based_price
from models.model_3_competitive import competitive_price
from utils.helpers import preprocess_data, create_lot_info
from utils.geospatial import calculate_distances, get_nearby_lots
from config import *

def preprocess_data(df):
    df['Timestamp'] = pd.to_datetime(
        df['LastUpdatedDate'] + ' ' + df['LastUpdatedTime'],
        format="%d-%m-%Y %H:%M:%S" 
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
    df['QueueLength'] = df['QueueLength'].fillna(0)  
    df['Traffic'] = df['Traffic'].fillna(1.0)
    df['IsSpecialDay'] = df['IsSpecialDay'].fillna(0).astype(bool)
    df['VehicleType'] = df['VehicleType'].fillna('car')
    df['VehicleWeight'] = df['VehicleType'].map(VEHICLE_WEIGHTS).fillna(1.0)
    return df.sort_values('Timestamp').reset_index(drop=True)

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

class PricingState(pw.Schema):
    lot_id: str
    last_price: float
    model: int

def update_prices(state, row):
    last_price = state.last_price if state.last_price is not None else BASE_PRICE
    model = state.model if state.model is not None else 2

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

pn.extension()

initial_time = pd.Timestamp.now()
source = ColumnDataSource({
    "t": [initial_time],
    "price": [30.0],
    "lot": ["Lot A"],
    "occupancy": [75],
    "capacity": [100]
})

plot = bokeh.plotting.figure(
    height=400,
    width=800,
    sizing_mode="stretch_width",
    x_axis_type="datetime",
    title="Real-Time Parking Price"
)

plot.line("t", "price", source=source, line_width=2, color="blue")

plot.add_tools(HoverTool(
    tooltips=[
        ("Lot", "@lot"),
        ("Price", "$@price"),
        ("Occupancy", "@occupancy/@capacity")
    ]
))

def update_data():
    new_data = {
        "t": [pd.Timestamp.now()],
        "price": [random.randint(10, 50)], 
        "lot": ["Lot A"],
        "occupancy": [random.randint(50, 100)],
        "capacity": [100]
    }
    source.stream(new_data, rollover=100)

pn.state.add_periodic_callback(update_data, period=1000)

# 5. Display the dashboard using a Production Template
template = pn.template.FastListTemplate(
    title="IIT Guwahati Capstone: Dynamic Pricing Simulation",
    main=[plot],
    accent_base_color="#0072B5", # Gives it a nice professional blue header
    header_background="#0072B5"
)
template.servable()

if not pn.state.cache.get('pathway_started', False):
    def run_pipeline():
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    
    threading.Thread(target=run_pipeline, daemon=True).start()
    pn.state.cache['pathway_started'] = True
