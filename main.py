
import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexKit Grid Simulator", layout="wide")
st.title("🔋 FlexKit: Real-time Carbon-Aware Dispatch Simulator")

st.markdown("""
Pulls live carbon intensity forecasts from the UK Carbon Intensity API  
and simulates a basic dispatch strategy for visualization.
""")

# --- Live Carbon Intensity Data ---
st.subheader("🌍 Carbon Intensity Forecast (UK-wide)")

try:
    r = requests.get("https://api.carbonintensity.org.uk/intensity")
    data = r.json()["data"]
    forecast_time = pd.to_datetime(data["from"])
    intensity_value = data["intensity"]["forecast"]

    st.success(f"Forecasted Carbon Intensity: {intensity_value} gCO₂/kWh at {forecast_time}")

except Exception as e:
    st.error(f"Failed to fetch live carbon data: {e}")
    intensity_value = 200  # fallback default

# --- Simulate Dispatch Based on Carbon ---
st.subheader("🔋 Simulate Simple Carbon-Based Strategy")

# User Inputs
battery_kWh = st.slider("Battery Capacity (kWh)", 5, 50, 20)
start_soc = st.slider("Starting SOC", 0.0, 1.0, 0.5, 0.05)
threshold = st.slider("Charge if carbon below (gCO₂/kWh)", 100, 400, 200)

# Generate 24h carbon signal
np.random.seed(1)
hours = pd.date_range("2025-01-01", periods=24, freq="H")
carbon = intensity_value + 60 * np.cos(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 20, 24)

# Dispatch simulation
soc = start_soc
soc_series = []
actions = []

for c in carbon:
    if c < threshold and soc < 1.0:
        action = "charge"
        soc += 0.05
    elif c > threshold + 100 and soc > 0.2:
        action = "discharge"
        soc -= 0.05
    else:
        action = "idle"
    soc = np.clip(soc, 0.0, 1.0)
    soc_series.append(soc)
    actions.append(action)

df = pd.DataFrame({
    "Time": hours,
    "Carbon": carbon,
    "SOC": soc_series,
    "Action": actions
})

# --- Plotting ---
st.subheader("📊 Simulation Results")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["Time"], df["Carbon"], label="Carbon Intensity", color="green")
ax.plot(df["Time"], df["SOC"], label="State of Charge", color="blue")
ax.set_ylabel("gCO₂/kWh / SOC")
ax.legend()
st.pyplot(fig)

st.dataframe(df)
