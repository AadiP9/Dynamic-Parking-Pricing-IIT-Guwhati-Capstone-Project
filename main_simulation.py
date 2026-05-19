import os
import random
import threading

import numpy as np
import pandas as pd
import panel as pn
import bokeh.plotting
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.palettes import Category10

from models.model1_1_baseline import baseline_price
from models.model1_2_demand import demand_based_price
from models.model_3_competitive import competitive_price
from utils.geospatial import calculate_distances, get_nearby_lots
from config import BASE_PRICE, MAX_DISTANCE_KM

# -------------------------------------------------------
# PANEL INITIALISATION
# -------------------------------------------------------
pn.extension(sizing_mode="stretch_width")

# -------------------------------------------------------
# SYNTHETIC LOT DEFINITIONS  (replaces the missing CSV)
# -------------------------------------------------------
# 5 parking lots around IIT Guwahati campus area
LOT_DEFINITIONS = [
    {"ParkingLotID": "Lot-A", "Capacity": 120, "Latitude": 26.1880, "Longitude": 91.6915},
    {"ParkingLotID": "Lot-B", "Capacity": 80,  "Latitude": 26.1920, "Longitude": 91.6950},
    {"ParkingLotID": "Lot-C", "Capacity": 60,  "Latitude": 26.1855, "Longitude": 91.6880},
    {"ParkingLotID": "Lot-D", "Capacity": 100, "Latitude": 26.1900, "Longitude": 91.6860},
    {"ParkingLotID": "Lot-E", "Capacity": 90,  "Latitude": 26.1940, "Longitude": 91.6900},
]

LOTS_DF = pd.DataFrame(LOT_DEFINITIONS)

# Build lot_info dict and distance matrix once
lot_info = {
    row["ParkingLotID"]: {
        "lat": row["Latitude"],
        "lon": row["Longitude"],
        "capacity": row["Capacity"],
    }
    for _, row in LOTS_DF.iterrows()
}

indices, distances = calculate_distances(
    LOTS_DF[["ParkingLotID", "Latitude", "Longitude"]].reset_index(drop=True)
)

# -------------------------------------------------------
# PRICING STATE  (per-lot, updated each tick)
# -------------------------------------------------------
lot_ids = [d["ParkingLotID"] for d in LOT_DEFINITIONS]
capacities = {d["ParkingLotID"]: d["Capacity"] for d in LOT_DEFINITIONS}

# Initialise state
state = {
    lot: {
        "price": BASE_PRICE,
        "occupancy": random.randint(20, 60),
        "queue": random.randint(0, 5),
        "traffic": random.uniform(20, 60),
        "is_special_day": False,
        "vehicle_weight": 1.0,
    }
    for lot in lot_ids
}

# -------------------------------------------------------
# BOKEH PLOT SETUP
# -------------------------------------------------------
PALETTE = Category10[max(len(lot_ids), 3)]

# One ColumnDataSource per lot
sources = {}
now = pd.Timestamp.now()
for i, lot in enumerate(lot_ids):
    sources[lot] = ColumnDataSource({
        "t":          [now - pd.Timedelta(seconds=1), now],
        "price":      [BASE_PRICE, BASE_PRICE],
        "occupancy":  [state[lot]["occupancy"], state[lot]["occupancy"]],
        "capacity":   [capacities[lot], capacities[lot]],
    })

plot = bokeh.plotting.figure(
    height=420,
    sizing_mode="stretch_width",
    x_axis_type="datetime",
    title="Real-Time Dynamic Parking Prices — IIT Guwahati",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)
plot.title.text_font_size = "15px"
plot.xaxis.axis_label = "Time"
plot.yaxis.axis_label = "Price (₹)"

renderers = []
for i, lot in enumerate(lot_ids):
    r = plot.line(
        "t", "price",
        source=sources[lot],
        line_width=2.5,
        color=PALETTE[i],
        name=lot,
    )
    plot.circle(
        "t", "price",
        source=sources[lot],
        size=6,
        color=PALETTE[i],
    )
    renderers.append((lot, [r]))

legend = Legend(items=[LegendItem(label=name, renderers=rs) for name, rs in renderers])
legend.click_policy = "hide"
legend.location = "top_left"
plot.add_layout(legend)

plot.add_tools(HoverTool(
    tooltips=[
        ("Lot",       "@name" if False else "$name"),
        ("Price",     "₹@price{0.2f}"),
        ("Occupancy", "@occupancy / @capacity"),
        ("Time",      "@t{%H:%M:%S}"),
    ],
    formatters={"@t": "datetime"},
    mode="mouse",
))

# -------------------------------------------------------
# MODEL SELECTOR
# -------------------------------------------------------
model_select = pn.widgets.Select(
    name="Pricing Model",
    options={
        "Model 1 — Baseline (Occupancy)": 1,
        "Model 2 — Demand-Based": 2,
        "Model 3 — Competitive": 3,
    },
    value=2,
    width=320,
)

reset_btn = pn.widgets.Button(name="Reset Prices", button_type="warning", width=160)

status_pane = pn.pane.Markdown("**Status:** Running ✅", width=300)

# -------------------------------------------------------
# REAL-TIME UPDATE CALLBACK
# -------------------------------------------------------
def simulate_tick():
    """Advance each lot's state by one synthetic tick and update sources."""
    chosen_model = model_select.value
    ts = pd.Timestamp.now()

    for lot in lot_ids:
        s = state[lot]
        cap = capacities[lot]

        # Simulate natural occupancy drift
        s["occupancy"] = max(0, min(cap, s["occupancy"] + random.randint(-5, 7)))
        s["queue"] = max(0, s["queue"] + random.randint(-1, 2))
        s["traffic"] = max(0.0, min(100.0, s["traffic"] + random.uniform(-5, 5)))
        s["is_special_day"] = random.random() < 0.05  # 5% chance special day

        occ = s["occupancy"]
        q   = s["queue"]
        traf = s["traffic"]
        spd  = s["is_special_day"]
        vw   = s["vehicle_weight"]
        last = s["price"]

        if chosen_model == 1:
            new_price = baseline_price(last, occ, cap)

        elif chosen_model == 2:
            new_price = demand_based_price(occ, cap, q, traf, spd, vw)

        else:  # model 3
            nearby = get_nearby_lots(lot, lot_info, distances, indices, MAX_DISTANCE_KM)
            comp_prices = [state[nl]["price"] for nl in nearby] or [BASE_PRICE]
            new_price = competitive_price(lot, last, occ, cap, comp_prices)

        s["price"] = new_price

        # Stream new point into the Bokeh source
        sources[lot].stream(
            {"t": [ts], "price": [new_price], "occupancy": [occ], "capacity": [cap]},
            rollover=120,
        )


def on_reset(event):
    for lot in lot_ids:
        state[lot]["price"] = BASE_PRICE
    status_pane.object = "**Status:** Prices reset ✅"


reset_btn.on_click(on_reset)

# Register the periodic callback (fires every 1000 ms)
pn.state.add_periodic_callback(simulate_tick, period=1000)

# -------------------------------------------------------
# LIVE STATS TABLE
# -------------------------------------------------------
def make_stats_df():
    rows = []
    for lot in lot_ids:
        s = state[lot]
        cap = capacities[lot]
        rows.append({
            "Lot": lot,
            "Price (₹)": f"{s['price']:.2f}",
            "Occupancy": f"{s['occupancy']} / {cap}",
            "Queue": s["queue"],
            "Traffic": f"{s['traffic']:.1f}",
        })
    return pd.DataFrame(rows)

stats_widget = pn.widgets.DataFrame(make_stats_df(), name="Current Stats", auto_edit=False, width=620)

def update_stats():
    stats_widget.value = make_stats_df()

pn.state.add_periodic_callback(update_stats, period=1500)

# -------------------------------------------------------
# DESCRIPTION PANEL
# -------------------------------------------------------
description = pn.pane.Markdown("""
## 🚗 Dynamic Parking Pricing System
**IIT Guwahati — Data Science Capstone Project**

This dashboard simulates real-time dynamic pricing across **5 parking lots** using three models:

| Model | Description |
|-------|-------------|
| **Model 1 — Baseline** | Simple linear adjustment based on occupancy ratio |
| **Model 2 — Demand-Based** | Combines occupancy, queue length, traffic, events & vehicle type |
| **Model 3 — Competitive** | Adds geospatial competitor analysis to optimise prices |

> Use the **dropdown** to switch models live. Click a legend entry to **show/hide** a lot.  
> Click **Reset Prices** to return all lots to the base price (₹10).
""", sizing_mode="stretch_width")

# -------------------------------------------------------
# LAYOUT & SERVE
# -------------------------------------------------------
controls = pn.Row(model_select, reset_btn, status_pane, sizing_mode="stretch_width")

template = pn.template.FastListTemplate(
    title="Dynamic Parking Pricing — IIT Guwahati Capstone",
    main=[
        description,
        controls,
        pn.pane.Bokeh(plot, sizing_mode="stretch_width"),
        pn.pane.Markdown("### Live Lot Statistics"),
        stats_widget,
    ],
    accent_base_color="#0072B5",
    header_background="#0072B5",
    theme="dark",
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5006))
    pn.serve(
        template,
        address="0.0.0.0",
        port=port,
        show=False,
        websocket_origin=["*"],
        allow_websocket_origin=["*"],
    )
