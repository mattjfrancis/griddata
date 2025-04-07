
import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexKit Real-Time Dispatch Explorer", layout="wide")
st.title("FlexKit: Real-Time Battery Dispatch Visualizer")

# --- Get Carbon Intensity Forecast (UK API) ---
def get_carbon_data():
    try:
        r = requests.get("https://api.carbonintensity.org.uk/intensity")
        data = r.json()["data"]
        base = data[0]["intensity"]["forecast"]
        carbon = base + 60 * np.cos(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 20, 24)
        return np.clip(carbon, 100, 500)
    except:
        return 250 + 60 * np.cos(np.linspace(0, 2 * np.pi, 24))

# --- Generate Synthetic Price Data ---
def get_price_data():
    return 100 + 50 * np.sin(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 10, 24)

# --- Simulation Setup ---
hours = pd.date_range("2025-01-01", periods=24, freq="H")
carbon = get_carbon_data()
price = get_price_data()
demand = np.clip(2 + 1.5 * np.sin(np.linspace(0, 2 * np.pi, 24)), 0, None)

st.sidebar.header("Battery Settings")
battery_kWh = st.sidebar.slider("Battery Capacity (kWh)", 10, 100, 20)
power_kW = st.sidebar.slider("Power Rating (kW)", 1, 20, 5)
soc_start = st.sidebar.slider("Starting SOC", 0.0, 1.0, 0.5, 0.05)

# --- Strategy Logic ---
soc = soc_start
soc_series = []
actions = []

for i in range(24):
    p, c = price[i], carbon[i]
    action = "idle"
    if p < 90 and soc < 1.0:
        action = "charge"
        soc += power_kW / battery_kWh
    elif p > 130 and soc > 0.2:
        action = "discharge"
        soc -= power_kW / battery_kWh
    soc = np.clip(soc, 0.0, 1.0)
    soc_series.append(soc)
    actions.append(action)

df = pd.DataFrame({
    "Hour": hours,
    "Price": price,
    "Carbon": carbon,
    "Demand": demand,
    "SOC": soc_series,
    "Action": actions
})

# --- Slider Control ---
t = st.slider("Select Hour", 0, 23, 0)

st.subheader(f"Hour: {t} | Action: {df['Action'][t]}")

# --- Visual Dashboard ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Hour"], df["SOC"], label="SOC", color="purple", linewidth=2)
ax.bar(df["Hour"], df["Price"] / max(df["Price"]), alpha=0.3, label="Price (scaled)", color="blue")
ax.bar(df["Hour"], df["Carbon"] / max(df["Carbon"]), alpha=0.3, label="Carbon (scaled)", color="green")
ax.axvline(df["Hour"][t], color="black", linestyle="--", linewidth=1)
ax.set_ylabel("State / Scaled Signals")
ax.set_xlabel("Hour")
ax.legend()
st.pyplot(fig)

# --- Animated Charge Bar ---
st.markdown("### Battery State")
st.progress(df["SOC"][t])

st.markdown(f'''
- Price: {df["Price"][t]:.1f} /MWh  
- Carbon: {df["Carbon"][t]:.0f} gCO2/kWh  
- SOC: {df["SOC"][t]:.2f}  
- Grid Flow: {"← Charging from Grid" if df["Action"][t] == "charge" else "→ Discharging to Grid" if df["Action"][t] == "discharge" else "Idle"}
''')
