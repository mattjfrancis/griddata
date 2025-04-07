
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import requests

st.set_page_config(page_title="FlexKit Dispatch Explorer", layout="wide")
st.title("FlexKit: Animated Dispatch with Strategy Controls")

# --- Forecast Data (24h, 15-min) ---
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

steps = 96
timestamps = pd.date_range("2025-01-01", periods=steps, freq="15min")
carbon = get_carbon_data()
price = get_price_data()
demand = np.clip(2 + 1.5 * np.sin(np.linspace(0, 2 * np.pi, steps)), 0, None)

# --- User Controls ---
st.sidebar.header("Battery Settings")
battery_kWh = st.sidebar.slider("Capacity (kWh)", 10, 100, 20)
power_kW = st.sidebar.slider("Power (kW)", 1, 20, 5)
soc_start = st.sidebar.slider("Starting SOC", 0.0, 1.0, 0.5, 0.05)

st.sidebar.header("Strategy Settings")
charge_price_limit = st.sidebar.slider("Charge if Price < ", 50, 150, 90)
discharge_price_limit = st.sidebar.slider("Discharge if Price > ", 100, 200, 130)
charge_carbon_limit = st.sidebar.slider("Charge if Carbon < ", 100, 300, 200)
discharge_carbon_limit = st.sidebar.slider("Discharge if Carbon > ", 300, 500, 400)
speed = st.sidebar.slider("Animation Speed (sec/frame)", 0.01, 0.5, 0.05)

# --- Dispatch Logic ---
soc = soc_start
soc_series, actions, grid_energy = [], [], []

for i in range(steps):
    p, c = price[i], carbon[i]
    action = "idle"
    if p < charge_price_limit and c < charge_carbon_limit and soc < 1.0:
        action = "charge"
        soc += power_kW / battery_kWh / 4
    elif (p > discharge_price_limit or c > discharge_carbon_limit) and soc > 0.2:
        action = "discharge"
        soc -= power_kW / battery_kWh / 4
    soc = np.clip(soc, 0.0, 1.0)
    soc_series.append(soc)
    actions.append(action)
    grid_energy.append(abs(soc_series[-1] - soc) * battery_kWh)

# --- DataFrame ---
df = pd.DataFrame({
    "Time": timestamps,
    "Price": price,
    "Carbon": carbon,
    "SOC": soc_series,
    "Action": actions,
    "Grid Energy (kWh)": grid_energy
})

# --- Animate ---
st.subheader("Dispatch Animation")

plot_placeholder = st.empty()
text_placeholder = st.empty()
progress_bar = st.progress(0)

for t in range(steps):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Time"][:t+1], df["SOC"][:t+1], label="SOC", color="purple")
    ax.plot(df["Time"], df["Price"] / max(df["Price"]), label="Price (scaled)", alpha=0.3, color="blue")
    ax.plot(df["Time"], df["Carbon"] / max(df["Carbon"]), label="Carbon (scaled)", alpha=0.3, color="green")
    ax.axvline(df["Time"][t], color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("SOC / Signals")
    ax.legend()
    plot_placeholder.pyplot(fig)

    action = df["Action"][t]
    flow = "← Charging" if action == "charge" else "→ Discharging" if action == "discharge" else "Idle"
    info = f"""**Time:** {df['Time'][t]}  
**SOC:** {df['SOC'][t]:.2f}  
**Action:** {action}  
**Grid Flow:** {flow}"""
    text_placeholder.markdown(info)
    progress_bar.progress(t / (steps - 1))
    time.sleep(speed)
