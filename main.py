
import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexKit Dispatch Demo", layout="wide")
st.title("FlexKit Battery Dispatch Demo")

mode = st.radio("Select Mode", ["Live Mode (Carbon API)", "Test Mode (Simulated)"])

def get_live_carbon():
    try:
        r = requests.get("https://api.carbonintensity.org.uk/intensity")
        data = r.json()["data"]
        forecast = data[0]["intensity"]["forecast"]
        return forecast + 60 * np.cos(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 10, 24)
    except Exception as e:
        st.error(f"Live data fetch failed: {e}")
        return 250 + 30 * np.sin(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 10, 24)

# Simulated or live forecast
np.random.seed(42)
hours = pd.date_range("2025-01-01", periods=24, freq="H")
price = 100 + 20 * np.sin(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 5, 24)
carbon = get_live_carbon() if mode == "Live Mode (Carbon API)" else 250 + 30 * np.sin(np.linspace(0, 2 * np.pi, 24))
demand = np.clip(2 + np.sin(np.linspace(0, 2 * np.pi, 24)), 0, None)

# Sidebar inputs
st.sidebar.header("Battery Settings")
capacity = st.sidebar.slider("Battery Capacity (kWh)", 5, 50, 20)
power = st.sidebar.slider("Power (kW)", 1, 10, 5)
soc_start = st.sidebar.slider("Initial SOC", 0.0, 1.0, 0.5, 0.05)
strategy = st.sidebar.selectbox("Dispatch Strategy", ["Blended (Price + Carbon)", "Price Arbitrage", "Carbon Minimizer"])

# Simulation
soc = soc_start
soc_series, action_series, energy_series = [], [], []

for i in range(24):
    p, c, d = price[i], carbon[i], demand[i]
    action = "idle"
    if strategy == "Price Arbitrage":
        action = "charge" if p < 90 and soc < 1.0 else "discharge" if p > 130 and soc > 0.2 else "idle"
    elif strategy == "Carbon Minimizer":
        action = "charge" if c < 200 and soc < 1.0 else "discharge" if c > 400 and soc > 0.2 else "idle"
    else:
        p_score = 1 - (p - min(price)) / (max(price) - min(price))
        c_score = 1 - (c - min(carbon)) / (max(carbon) - min(carbon))
        blended = 0.5 * p_score + 0.5 * c_score
        action = "charge" if blended > 0.7 and soc < 1.0 else "discharge" if blended < 0.3 and soc > 0.2 else "idle"

    prev_soc = soc
    if action == "charge":
        soc = min(1.0, soc + (power / capacity) * 0.5)
    elif action == "discharge":
        soc = max(0.0, soc - (power / capacity) * 0.5)

    soc_series.append(soc)
    action_series.append(action)
    energy_series.append(abs(soc - prev_soc) * capacity)

df = pd.DataFrame({
    "Time": hours,
    "Price": price,
    "Carbon": carbon,
    "Demand": demand,
    "SOC": soc_series,
    "Action": action_series,
    "Grid Energy (kWh)": energy_series
})

# Summary
total_cost = (df["Grid Energy (kWh)"] * df["Price"] / 1000).sum()
total_co2 = (df["Grid Energy (kWh)"] * df["Carbon"] / 1000).sum()

st.subheader("Summary")
st.markdown(f"**Total Cost:** £{total_cost:.2f}")
st.markdown(f"**Total Emissions:** {total_co2:.2f} kg CO₂")
st.markdown(f"**Total Energy:** {df['Grid Energy (kWh)'].sum():.2f} kWh")

# Plot
fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
ax[0].plot(df["Time"], df["Price"], label="Price", color="blue")
ax[1].plot(df["Time"], df["Carbon"], label="Carbon", color="green")
ax[2].plot(df["Time"], df["SOC"], label="SOC", color="purple")
ax[2].scatter(df["Time"], [1 if a=="charge" else -1 if a=="discharge" else 0 for a in df["Action"]],
              color=["blue" if a=="charge" else "red" if a=="discharge" else "gray" for a in df["Action"]],
              label="Action", zorder=3)
for a in ax: a.legend()
st.pyplot(fig)

st.subheader("Dispatch Table")
st.dataframe(df)
