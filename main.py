import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexKit Simulator", layout="wide")

# Title
st.title("🔋 FlexKit Dispatch Strategy Simulator")
st.markdown("Simulate how a battery dispatches based on energy **price**, **carbon intensity**, and strategy preferences.")

# Sidebar configuration
st.sidebar.header("⚙️ Strategy Settings")
price_low = st.sidebar.slider("🔻 Charge Below Price (£/MWh)", 10, 100, 50)
price_high = st.sidebar.slider("🔺 Discharge Above Price (£/MWh)", 100, 300, 150)
carbon_low = st.sidebar.slider("🟢 Green Threshold (gCO₂/kWh)", 50, 300, 200)
carbon_high = st.sidebar.slider("🔴 Dirty Threshold (gCO₂/kWh)", 300, 600, 400)
carbon_weight = st.sidebar.slider("⚖️ Carbon vs Price Weight", 0.0, 1.0, 0.5)

# Battery config
battery_config = {
    "charge_price_threshold": price_low,
    "discharge_price_threshold": price_high,
    "green_threshold": carbon_low,
    "dirty_threshold": carbon_high,
    "carbon_weight": carbon_weight,
    "charge_efficiency": 0.95,
    "discharge_efficiency": 0.9,
    "step_size": 0.05
}

# Generate realistic daily energy price/carbon cycle
def generate_daily_cycle(amplitude=70, base=100, noise=10, phase_shift=0):
    hours = np.arange(24)
    cycle = base + amplitude * np.sin((hours - phase_shift) * np.pi / 12)
    noise_component = np.random.normal(0, noise, size=24)
    return np.clip(cycle + noise_component, 0, None)

# Refresh data button
if st.button("🔄 Regenerate Grid Data"):
    st.session_state["new_data"] = True

# Maintain consistent data unless refreshed
if "prices" not in st.session_state or st.session_state.get("new_data"):
    st.session_state["prices"] = generate_daily_cycle(phase_shift=18)  # evening peak
    st.session_state["carbon"] = generate_daily_cycle(amplitude=100, base=300, noise=25, phase_shift=16)
    st.session_state["timestamps"] = pd.date_range("2025-01-01", periods=24, freq="H")
    st.session_state["new_data"] = False

prices = st.session_state["prices"]
carbon = st.session_state["carbon"]
time_range = st.session_state["timestamps"]

# Helper functions
def update_soc(soc, action, config):
    step = config["step_size"]
    if action == "charge":
        return min(1.0, soc + step * config["charge_efficiency"])
    elif action == "discharge":
        return max(0.0, soc - step / config["discharge_efficiency"])
    return soc

def blended_strategy(prices, carbon, soc, battery_config):
    schedule = []
    for t, (p, c) in enumerate(zip(prices, carbon)):
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
            "blended_score": round(blended_score, 2)
        })

        soc = update_soc(soc, action, battery_config)

    return pd.DataFrame(schedule)

# Run simulation
soc_start = 0.5
df_schedule = blended_strategy(prices, carbon, soc_start, battery_config)

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Simulation Results")

    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axs[0].plot(time_range, df_schedule["price"], label="Price (£/MWh)")
    axs[0].set_ylabel("Price")
    axs[0].legend()

    axs[1].plot(time_range, df_schedule["carbon"], label="Carbon Intensity (gCO₂/kWh)", color="green")
    axs[1].set_ylabel("Carbon")
    axs[1].legend()

    axs[2].plot(time_range, df_schedule["soc"], label="State of Charge", color="purple")
    action_colors = df_schedule["action"].map({"charge": "blue", "discharge": "red", "idle": "gray"})
    action_vals = df_schedule["action"].map({"charge": 1, "discharge": -1, "idle": 0})
    axs[2].scatter(time_range, action_vals, color=action_colors, label="Action", zorder=3)
    axs[2].set_ylabel("SOC / Action")
    axs[2].legend()

    plt.xlabel("Time")
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("📋 Dispatch Log")
    st.dataframe(df_schedule[["timestamp", "action", "price", "carbon", "soc", "blended_score"]].style.format({
        "price": "£{:.0f}",
        "carbon": "{:.0f} g",
        "soc": "{:.2f}"
    }))
