
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import requests

st.set_page_config(page_title="FlexKit Cloud Dispatch", layout="wide")
st.title("FlexKit: Market-Based Flexibility + Cloud Dashboard")

# --- Carbon & Price Forecast ---
def get_carbon_data():
    try:
        r = requests.get("https://api.carbonintensity.org.uk/intensity")
        data = r.json()["data"]
        base = data[0]["intensity"]["forecast"]
        carbon = base + 60 * np.cos(np.linspace(0, 2 * np.pi, 96)) + np.random.normal(0, 20, 96)
        return np.clip(carbon, 100, 500)
    except:
        return 250 + 60 * np.cos(np.linspace(0, 2 * np.pi, 96))

def get_price_data():
    return 100 + 40 * np.sin(np.linspace(0, 2 * np.pi, 96)) + np.random.normal(0, 10, 96)

def get_reg_market_price():
    return 0.3 + 0.2 * np.cos(np.linspace(0, 2 * np.pi, 96)) + np.random.normal(0, 0.05, 96)

# --- Forecast Setup ---
steps = 96
timestamps = pd.date_range("2025-01-01", periods=steps, freq="15min")
carbon = get_carbon_data()
price = get_price_data()
reg_market_price = get_reg_market_price()

# --- User Inputs ---
st.sidebar.header("Battery Settings")
battery_kWh = st.sidebar.slider("Battery Capacity", 10, 100, 30)
power_kW = st.sidebar.slider("Power Rating", 1, 20, 5)
soc_start = st.sidebar.slider("Start SOC", 0.0, 1.0, 0.5, 0.05)

st.sidebar.header("Frequency Regulation")
participate = st.sidebar.checkbox("Enable Grid Support (Regulation)", True)
max_reg_share = st.sidebar.slider("Max Share for Regulation", 0.0, 0.5, 0.1)
speed = st.sidebar.slider("Animation Speed", 0.01, 0.3, 0.05)

# --- Simulate Dispatch ---
soc = soc_start
soc_series = []
actions = []
grid_energy = []
reg_revenue = []
carbon_offset = []

for i in range(steps):
    p, c, reg_price = price[i], carbon[i], reg_market_price[i]
    action = "idle"

    if p < 90 and soc < 1.0:
        action = "charge"
        soc += power_kW / battery_kWh / 4
        energy_used = power_kW / 4
        grid_energy.append(energy_used)
        carbon_offset.append(0)
        reg_revenue.append(0)
    elif p > 130 and soc > 0.2:
        action = "discharge"
        soc -= power_kW / battery_kWh / 4
        energy_out = power_kW / 4
        grid_energy.append(0)
        carbon_offset.append(energy_out * c / 1000)
        reg_revenue.append(0)
    else:
        # idle but participate in regulation
        grid_energy.append(0)
        carbon_offset.append(0)
        if participate:
            capacity = battery_kWh * max_reg_share
            reg_revenue.append(capacity * reg_price / 4)
        else:
            reg_revenue.append(0)

    soc = np.clip(soc, 0.0, 1.0)
    soc_series.append(soc)
    actions.append(action)

# --- Frame Data ---
df = pd.DataFrame({
    "Time": timestamps,
    "Price": price,
    "Carbon": carbon,
    "SOC": soc_series,
    "Action": actions,
    "Grid Energy (kWh)": grid_energy,
    "Reg Revenue (£)": reg_revenue,
    "CO2 Offset (kg)": carbon_offset
})

# --- Dashboard Overview ---
st.subheader("📊 Strategy Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Total Grid Energy", f"{df['Grid Energy (kWh)'].sum():.2f} kWh")
col2.metric("Carbon Offset", f"{np.sum(df['CO2 Offset (kg)']):.2f} kg")
col3.metric("Frequency Revenue", f"£{np.sum(df['Reg Revenue (£)']):.2f}")

# --- Simulated Cloud Sync ---
st.success("🔗 Cloud Sync: FlexKit Edge Dispatch connected to dashboard.flexkit.energy")
st.caption("Data is simulated for demonstration purposes.")

# --- Animate ---
plot = st.empty()
progress = st.progress(0)
for t in range(steps):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Time"][:t+1], df["SOC"][:t+1], label="SOC", color="purple")
    ax.plot(df["Time"], df["Price"] / max(df["Price"]), label="Price (scaled)", color="blue", alpha=0.3)
    ax.plot(df["Time"], df["Carbon"] / max(df["Carbon"]), label="Carbon (scaled)", color="green", alpha=0.3)
    ax.plot(df["Time"], df["Reg Revenue (£)"] / max(df["Reg Revenue (£)"] + 1e-5), label="Reg Revenue (scaled)", alpha=0.3, color="orange")
    ax.axvline(df["Time"][t], color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("SOC & Scaled Metrics")
    ax.legend()
    plot.pyplot(fig)
    progress.progress(t / (steps - 1))
    time.sleep(speed)
