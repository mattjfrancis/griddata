
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="FlexKit Animated Dispatch", layout="wide")
st.title("FlexKit: Animated Battery Dispatch Simulation") 

# --- Get Carbon Intensity Forecast (UK API) ---
def get_carbon_data():
    try:
        r = requests.get("https://api.carbonintensity.org.uk/intensity")
        data = r.json()["data"]
        base = data[0]["intensity"]["forecast"]
        carbon = base + 60 * np.cos(np.linspace(0, 2 * np.pi, 96)) + np.random.normal(0, 20, 96)
        return np.clip(carbon, 100, 500)
    except:
        return 250 + 60 * np.cos(np.linspace(0, 2 * np.pi, 96))

# --- Synthetic Price Signal ---
def get_price_data():
    return 100 + 40 * np.sin(np.linspace(0, 2 * np.pi, 96)) + np.random.normal(0, 10, 96)

# --- Setup ---
steps = 96  # 15-min intervals for 24h
timestamps = pd.date_range("2025-01-01", periods=steps, freq="15min")
carbon = get_carbon_data()
price = get_price_data()
demand = np.clip(2 + 1.5 * np.sin(np.linspace(0, 2 * np.pi, steps)), 0, None)

st.sidebar.header("Battery Settings")
battery_kWh = st.sidebar.slider("Battery Capacity (kWh)", 10, 100, 20)
power_kW = st.sidebar.slider("Power Rating (kW)", 1, 20, 5)
soc_start = st.sidebar.slider("Starting SOC", 0.0, 1.0, 0.5, 0.05)
speed = st.sidebar.slider("Animation Speed (sec/frame)", 0.01, 0.5, 0.1)

# --- Dispatch Simulation ---
soc = soc_start
soc_series, actions = [], []

for i in range(steps):
    p, c = price[i], carbon[i]
    action = "idle"
    if p < 90 and soc < 1.0:
        action = "charge"
        soc += power_kW / battery_kWh / 4
    elif p > 130 and soc > 0.2:
        action = "discharge"
        soc -= power_kW / battery_kWh / 4
    soc = np.clip(soc, 0.0, 1.0)
    soc_series.append(soc)
    actions.append(action)

df = pd.DataFrame({
    "Time": timestamps,
    "Price": price,
    "Carbon": carbon,
    "Demand": demand,
    "SOC": soc_series,
    "Action": actions
})

# --- Animate Frame-by-Frame ---
st.subheader("Battery Dispatch Animation")

plot_placeholder = st.empty()
text_placeholder = st.empty()
progress_bar = st.progress(0)

for t in range(steps):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Time"][:t+1], df["SOC"][:t+1], label="SOC", color="purple")
    ax.plot(df["Time"], df["Price"] / max(df["Price"]), label="Price (scaled)", alpha=0.3, color="blue")
    ax.plot(df["Time"], df["Carbon"] / max(df["Carbon"]), label="Carbon (scaled)", alpha=0.3, color="green")
    ax.axvline(df["Time"][t], color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("SOC / Scaled Signals")
    ax.set_xlabel("Time")
    ax.legend()
    plot_placeholder.pyplot(fig)

    action = df["Action"][t]
    flow_text = "← Charging" if action == "charge" else "→ Discharging" if action == "discharge" else "Idle"
    text_placeholder.markdown(f"**Time:** {df['Time'][t]}  
**SOC:** {df['SOC'][t]:.2f}  
**Action:** {action}  
**Grid Flow:** {flow_text}")
    progress_bar.progress(t / (steps - 1))
    time.sleep(speed)
