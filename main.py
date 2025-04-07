
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="FlexKit Strategy Dashboard", layout="wide")
st.title("FlexKit Dispatch Comparison Dashboard")

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

# --- Price Signal ---
def get_price_data():
    return 100 + 40 * np.sin(np.linspace(0, 2 * np.pi, 96)) + np.random.normal(0, 10, 96)

# --- Parameters ---
steps = 96
timestamps = pd.date_range("2025-01-01", periods=steps, freq="15min")
carbon = get_carbon_data()
price = get_price_data()
demand = np.clip(2 + 1.5 * np.sin(np.linspace(0, 2 * np.pi, steps)), 0, None)

st.sidebar.header("Battery Settings")
battery_kWh = st.sidebar.slider("Battery Capacity (kWh)", 10, 100, 20)
power_kW = st.sidebar.slider("Power Rating (kW)", 1, 20, 5)
soc_start = st.sidebar.slider("Starting SOC", 0.0, 1.0, 0.5, 0.05)

strategies = {
    "Price Arbitrage": lambda p, c, soc: "charge" if p < 90 and soc < 1.0 else "discharge" if p > 130 and soc > 0.2 else "idle",
    "Carbon Minimizer": lambda p, c, soc: "charge" if c < 200 and soc < 1.0 else "discharge" if c > 400 and soc > 0.2 else "idle",
    "Blended": lambda p, c, soc: (
        "charge" if (0.5 * (1 - (p - min(price))/(max(price)-min(price))) + 0.5 * (1 - (c - min(carbon))/(max(carbon)-min(carbon))) > 0.7 and soc < 1.0)
        else "discharge" if (0.5 * (1 - (p - min(price))/(max(price)-min(price))) + 0.5 * (1 - (c - min(carbon))/(max(carbon)-min(carbon))) < 0.3 and soc > 0.2)
        else "idle"
    )
}

# --- Run Simulation For Each Strategy ---
results = {}

for name, logic in strategies.items():
    soc = soc_start
    soc_series = []
    actions = []
    grid_energy = []
    for i in range(steps):
        p, c = price[i], carbon[i]
        action = logic(p, c, soc)
        if action == "charge":
            soc += power_kW / battery_kWh / 4
        elif action == "discharge":
            soc -= power_kW / battery_kWh / 4
        soc = np.clip(soc, 0.0, 1.0)
        soc_series.append(soc)
        actions.append(action)
        grid_energy.append(abs(soc_series[-1] - soc) * battery_kWh)
    df = pd.DataFrame({
        "Time": timestamps,
        "Price": price,
        "Carbon": carbon,
        "Demand": demand,
        "SOC": soc_series,
        "Action": actions,
        "Grid Energy": grid_energy
    })
    df["Strategy"] = name
    df["Cost"] = df["Grid Energy"] * df["Price"] / 1000
    df["Emissions"] = df["Grid Energy"] * df["Carbon"] / 1000
    results[name] = df

# --- Combine and Show Comparison Dashboard ---
combined_df = pd.concat(results.values())

st.subheader("Comparison Dashboard")
selected_strategy = st.selectbox("Select Strategy to Inspect", list(strategies.keys()))
df = results[selected_strategy]

col1, col2, col3 = st.columns(3)
col1.metric("Total Cost", f"{df['Cost'].sum():.2f}")
col2.metric("Total Emissions", f"{df['Emissions'].sum():.2f} kg CO₂")
col3.metric("Total Grid Energy", f"{df['Grid Energy'].sum():.2f} kWh")

# --- Plot Comparisons ---
st.subheader("SOC Comparison")
fig, ax = plt.subplots(figsize=(10, 5))
for name, df in results.items():
    ax.plot(df["Time"], df["SOC"], label=name)
ax.legend()
ax.set_ylabel("State of Charge")
st.pyplot(fig)

st.subheader("Cost & Emissions Over Time")
fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
for name, df in results.items():
    ax[0].plot(df["Time"], df["Cost"].cumsum(), label=name)
    ax[1].plot(df["Time"], df["Emissions"].cumsum(), label=name)
ax[0].set_ylabel("Cumulative Cost (£)")
ax[1].set_ylabel("Cumulative Emissions (kg CO₂)")
ax[1].set_xlabel("Time")
ax[0].legend()
ax[1].legend()
st.pyplot(fig)
