import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Page config
st.set_page_config(page_title="FlexKit Dispatch Strategy Simulator", layout="wide")

st.title("🔋 FlexKit Dispatch Strategy Simulator")
st.markdown("Simulate and visualize flexible energy asset behavior based on price and carbon intensity.")

# User controls
carbon_weight = st.slider("Carbon vs Price Priority", 0.0, 1.0, 0.5, step=0.05)
charge_price_threshold = st.slider("Charge if Price Below (£/MWh)", 10, 150, 50)
discharge_price_threshold = st.slider("Discharge if Price Above (£/MWh)", 50, 250, 150)
green_threshold = st.slider("Charge if Carbon Below (gCO₂/kWh)", 50, 400, 200)
dirty_threshold = st.slider("Discharge if Carbon Above (gCO₂/kWh)", 100, 600, 400)

# Battery config
battery_config = {
    "charge_price_threshold": charge_price_threshold,
    "discharge_price_threshold": discharge_price_threshold,
    "green_threshold": green_threshold,
    "dirty_threshold": dirty_threshold,
    "carbon_weight": carbon_weight,
    "charge_efficiency": 0.95,
    "discharge_efficiency": 0.9,
    "step_size": 0.05
}

# Helper functions
def update_soc(soc, action, config):
    step = config["step_size"]
    if action == "charge":
        return min(1.0, soc + step * config["charge_efficiency"])
    elif action == "discharge":
        return max(0.0, soc - step / config["discharge_efficiency"])
    return soc

def blended_strategy(prices, carbon, soc, battery_config):
    score_weight = battery_config["carbon_weight"]
    schedule = []

    for t, (p, c) in enumerate(zip(prices, carbon)):
        price_score = 1 - (p - min(prices)) / (max(prices) - min(prices))
        carbon_score = 1 - (c - min(carbon)) / (max(carbon) - min(carbon))
        blended_score = score_weight * carbon_score + (1 - score_weight) * price_score

        if blended_score > 0.7 and soc < 1.0:
            action = "charge"
        elif blended_score < 0.3 and soc > 0.2:
            action = "discharge"
        else:
            action = "idle"

        schedule.append({
            "time": t,
            "action": action,
            "blended_score": round(blended_score, 2),
            "price": p,
            "carbon": c,
            "soc": soc
        })

        soc = update_soc(soc, action, battery_config)

    return pd.DataFrame(schedule)

# Simulation block
soc_start = 0.5
prices = np.random.uniform(30, 200, 24)
carbon = np.random.uniform(100, 500, 24)
time_range = pd.date_range("2025-01-01", periods=24, freq="H")

df_schedule = blended_strategy(prices, carbon, soc_start, battery_config)
df_schedule["timestamp"] = time_range

# Plot results
fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
axs[0].plot(df_schedule["timestamp"], df_schedule["price"], label="Price (£/MWh)")
axs[0].set_ylabel("Price")
axs[0].legend()

axs[1].plot(df_schedule["timestamp"], df_schedule["carbon"], label="Carbon Intensity (gCO₂/kWh)", color="green")
axs[1].set_ylabel("Carbon")
axs[1].legend()

axs[2].plot(df_schedule["timestamp"], df_schedule["soc"], label="State of Charge", color="purple")
axs[2].scatter(df_schedule["timestamp"],
               df_schedule["action"].apply(lambda x: 1 if x=="charge" else (-1 if x=="discharge" else 0)),
               label="Action",
               c=df_schedule["action"].apply(lambda x: "blue" if x=="charge" else ("red" if x=="discharge" else "gray")))
axs[2].set_ylabel("SOC & Action")
axs[2].legend()

plt.xlabel("Time")
plt.tight_layout()
st.pyplot(fig)

st.markdown("---")
st.dataframe(df_schedule[["timestamp", "action", "price", "carbon", "soc"]].round(2))
