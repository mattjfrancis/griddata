import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexKit Simulator", layout="wide")

st.title("🔋 FlexKit Dispatch Strategy Simulator")
st.markdown("Simulate how a battery dispatches based on energy **price**, **carbon intensity**, custom **user demand profiles**, and **battery discharge**.")

# Sidebar: Region and Battery Settings
st.sidebar.header("🌍 Region Settings")
region = st.sidebar.selectbox("Select Region", ["UK", "Germany", "Texas", "California", "France"])

region_profiles = {
    "UK": {"price_base": 120, "carbon_base": 250, "price_amp": 60, "carbon_amp": 100, "noise": 15},
    "Germany": {"price_base": 90, "carbon_base": 300, "price_amp": 50, "carbon_amp": 80, "noise": 15},
    "Texas": {"price_base": 60, "carbon_base": 400, "price_amp": 80, "carbon_amp": 120, "noise": 20},
    "California": {"price_base": 100, "carbon_base": 200, "price_amp": 70, "carbon_amp": 60, "noise": 10},
    "France": {"price_base": 80, "carbon_base": 100, "price_amp": 40, "carbon_amp": 30, "noise": 5},
}

profile = region_profiles[region]

st.sidebar.header("🔋 Battery Settings")
battery_capacity_kWh = st.sidebar.slider("Battery Capacity (kWh)", 5, 100, 20)
power_rating_kW = st.sidebar.slider("Power Rating (kW)", 1, 50, 5)
passive_discharge = st.sidebar.slider("Passive Discharge Rate (% per hour)", 0.0, 2.0, 0.2) / 100

# Custom user demand by time block
st.sidebar.header("⚡ User Load Profile")
morning_demand = st.sidebar.slider("6am–12pm Demand (kW)", 0.0, 10.0, 2.0)
afternoon_demand = st.sidebar.slider("12pm–6pm Demand (kW)", 0.0, 10.0, 3.0)
evening_demand = st.sidebar.slider("6pm–12am Demand (kW)", 0.0, 10.0, 5.0)
night_demand = st.sidebar.slider("12am–6am Demand (kW)", 0.0, 10.0, 1.0)

# Strategy config
st.sidebar.header("⚙️ Strategy Preferences")
price_low = st.sidebar.slider("🔻 Charge Below Price (£/MWh)", 10, 100, 50)
price_high = st.sidebar.slider("🔺 Discharge Above Price (£/MWh)", 100, 300, 150)
carbon_low = st.sidebar.slider("🟢 Green Threshold (gCO₂/kWh)", 50, 300, 200)
carbon_high = st.sidebar.slider("🔴 Dirty Threshold (gCO₂/kWh)", 300, 600, 400)
carbon_weight = st.sidebar.slider("⚖️ Carbon vs Price Weight", 0.0, 1.0, 0.5)

battery_config = {
    "charge_price_threshold": price_low,
    "discharge_price_threshold": price_high,
    "green_threshold": carbon_low,
    "dirty_threshold": carbon_high,
    "carbon_weight": carbon_weight,
    "charge_efficiency": 0.95,
    "discharge_efficiency": 0.9,
    "step_size": power_rating_kW / battery_capacity_kWh / 2,
    "passive_discharge": passive_discharge
}

# Generate region-aware daily cycle
def generate_daily_cycle(amplitude, base, noise, phase_shift=0):
    hours = np.arange(24)
    cycle = base + amplitude * np.sin((hours - phase_shift) * np.pi / 12)
    noise_component = np.random.normal(0, noise, size=24)
    return np.clip(cycle + noise_component, 0, None)

# Build user demand profile
def generate_user_demand():
    profile = []
    for hour in range(24):
        if 6 <= hour < 12:
            demand = morning_demand
        elif 12 <= hour < 18:
            demand = afternoon_demand
        elif 18 <= hour < 24:
            demand = evening_demand
        else:
            demand = night_demand
        profile.append(demand / battery_capacity_kWh)  # convert to % of capacity
    return profile

# Refresh on region change
if "last_region" not in st.session_state or st.session_state["last_region"] != region:
    st.session_state["prices"] = generate_daily_cycle(profile["price_amp"], profile["price_base"], profile["noise"], phase_shift=18)
    st.session_state["carbon"] = generate_daily_cycle(profile["carbon_amp"], profile["carbon_base"], profile["noise"], phase_shift=16)
    st.session_state["timestamps"] = pd.date_range("2025-01-01", periods=24, freq="H")
    st.session_state["last_region"] = region

prices = st.session_state["prices"]
carbon = st.session_state["carbon"]
user_demand_profile = generate_user_demand()
time_range = st.session_state["timestamps"]

# Simulation logic
def update_soc(soc, action, config, demand_kWh):
    step = config["step_size"]
    soc -= config["passive_discharge"]  # passive loss
    soc -= demand_kWh                   # user demand
    soc = max(0.0, soc)

    if action == "charge":
        soc = min(1.0, soc + step * config["charge_efficiency"])
    elif action == "discharge":
        soc = max(0.0, soc - step / config["discharge_efficiency"])

    return soc

def blended_strategy(prices, carbon, user_demand, soc, battery_config):
    schedule = []
    for t, (p, c, demand_kWh) in enumerate(zip(prices, carbon, user_demand)):
        price_score = 1 - (p - min(prices)) / (max(prices) - min(prices))
        carbon_score = 1 - (c - min(carbon)) / (max(carbon) - min(carbon))
        blended_score = battery_config["carbon_weight"] * carbon_score + (1 - battery_config["carbon_weight"]) * price_score

        if blended_score > 0.7 and soc < 1.0:
            action = "charge"
        elif blended_score < 0.3 and soc > 0.2:
            action = "discharge"
        else:
            action = "idle"

        schedule.append({
            "time": t,
            "timestamp": time_range[t],
            "action": action,
            "price": p,
            "carbon": c,
            "soc": soc,
            "user_demand_kWh": demand_kWh * battery_capacity_kWh,
            "blended_score": round(blended_score, 2)
        })

        soc = update_soc(soc, action, battery_config, demand_kWh)

    return pd.DataFrame(schedule)

# Run simulation
soc_start = 0.5
df_schedule = blended_strategy(prices, carbon, user_demand_profile, soc_start, battery_config)

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Simulation Results")

    fig, axs = plt.subplots(4, 1, figsize=(10, 10), sharex=True)

    axs[0].plot(time_range, df_schedule["price"], label="Price (£/MWh)")
    axs[0].set_ylabel("Price")
    axs[0].legend()

    axs[1].plot(time_range, df_schedule["carbon"], label="Carbon Intensity (gCO₂/kWh)", color="green")
    axs[1].set_ylabel("Carbon")
    axs[1].legend()

    axs[2].plot(time_range, df_schedule["user_demand_kWh"], label="User Demand (kWh)", color="orange")
    axs[2].set_ylabel("Demand")
    axs[2].legend()

    axs[3].plot(time_range, df_schedule["soc"], label="State of Charge", color="purple")
    action_colors = df_schedule["action"].map({"charge": "blue", "discharge": "red", "idle": "gray"})
    action_vals = df_schedule["action"].map({"charge": 1, "discharge": -1, "idle": 0})
    axs[3].scatter(time_range, action_vals, color=action_colors, label="Action", zorder=3)
    axs[3].set_ylabel("SOC / Action")
    axs[3].legend()

    plt.xlabel("Time")
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("📋 Dispatch Log")
    st.dataframe(df_schedule[["timestamp", "action", "price", "carbon", "user_demand_kWh", "soc", "blended_score"]].style.format({
        "price": "£{:.0f}",
        "carbon": "{:.0f} g",
        "soc": "{:.2f}",
        "user_demand_kWh": "{:.2f}"
    }))

