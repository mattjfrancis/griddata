import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexKit Unified App", layout="wide")

# Sidebar navigation
st.sidebar.title("🔧 FlexKit Tools")
page = st.sidebar.radio("Navigate to", ["Home", "Strategy Comparison", "Emissions Explorer", "Battery Sizing Tool"])

# ================== PAGE: HOME ==================
if page == "Home":
    st.title("🔋 FlexKit Energy Dispatch Simulator")

    # Region selection and price/carbon generation
    region_profiles = {
        "UK": {"price_base": 120, "carbon_base": 250, "price_amp": 60, "carbon_amp": 100, "noise": 15},
        "Germany": {"price_base": 90, "carbon_base": 300, "price_amp": 50, "carbon_amp": 80, "noise": 15},
        "Texas": {"price_base": 60, "carbon_base": 400, "price_amp": 80, "carbon_amp": 120, "noise": 20},
        "California": {"price_base": 100, "carbon_base": 200, "price_amp": 70, "carbon_amp": 60, "noise": 10},
        "France": {"price_base": 80, "carbon_base": 100, "price_amp": 40, "carbon_amp": 30, "noise": 5},
    }

    region = st.selectbox("🌍 Select Region", list(region_profiles.keys()))
    profile = region_profiles[region]

    def generate_daily_cycle(amplitude, base, noise, phase_shift=0):
        hours = np.arange(24)
        cycle = base + amplitude * np.sin((hours - phase_shift) * np.pi / 12)
        noise_component = np.random.normal(0, noise, size=24)
        return np.clip(cycle + noise_component, 0, None)

    prices = generate_daily_cycle(profile["price_amp"], profile["price_base"], profile["noise"], phase_shift=18)
    carbon = generate_daily_cycle(profile["carbon_amp"], profile["carbon_base"], profile["noise"], phase_shift=16)
    time_range = pd.date_range("2025-01-01", periods=24, freq="H")

    # Dispatch Strategy
    st.subheader("⚙️ Strategy Configuration")
    price_low = st.slider("🔻 Charge Below Price (£/MWh)", 10, 100, 50)
    price_high = st.slider("🔺 Discharge Above Price (£/MWh)", 100, 300, 150)

    st.subheader("📈 Simulation Result")

    def run_dispatch(prices, carbon, soc=0.5):
        schedule = []
        for t, p in enumerate(prices):
            if p < price_low and soc < 1.0:
                action = "charge"
                soc = min(1.0, soc + 0.05)
            elif p > price_high and soc > 0.2:
                action = "discharge"
                soc = max(0.0, soc - 0.05)
            else:
                action = "idle"
            schedule.append({"time": t, "timestamp": time_range[t], "price": p, "carbon": carbon[t], "soc": soc, "action": action})
        return pd.DataFrame(schedule)

    df = run_dispatch(prices, carbon)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["timestamp"], df["soc"], label="State of Charge")
    ax.set_ylabel("SOC")
    ax.set_title("Battery Dispatch Simulation")
    st.pyplot(fig)
    st.dataframe(df)

# ================== STRATEGY COMPARISON ==================
elif page == "Strategy Comparison":
    st.title("📊 Strategy Comparison")

    st.sidebar.header("⚖️ Scoring Weights")
    cost_weight = st.sidebar.slider("Weight for Cost", 0.0, 1.0, 0.5)
    carbon_weight = 1.0 - cost_weight
    st.sidebar.markdown(f"🔁 Carbon Weight = **{carbon_weight:.2f}**")

    # Corrected strategy results
    results = pd.DataFrame([
        {"Strategy": "Blended (Price + Carbon)", "Energy": 14.6, "Cost": 9.32, "CO2": 7.1},
        {"Strategy": "Tariff Avoidance Only", "Energy": 12.3, "Cost": 6.85, "CO2": 8.5},
        {"Strategy": "Price Arbitrage", "Energy": 15.1, "Cost": 11.2, "CO2": 9.9},
        {"Strategy": "Carbon Minimizer", "Energy": 13.8, "Cost": 8.90, "CO2": 5.3}
    ])

    results["Score"] = (
        cost_weight * (1 - (results["Cost"] - results["Cost"].min()) / (results["Cost"].max() - results["Cost"].min())) +
        carbon_weight * (1 - (results["CO2"] - results["CO2"].min()) / (results["CO2"].max() - results["CO2"].min()))
    )
    best_idx = results["Score"].idxmax()
    results["🏆 Best"] = ""
    results.loc[best_idx, "🏆 Best"] = "✅"

    st.subheader("🏁 Strategy Performance")
    st.dataframe(results[["Strategy", "Energy", "Cost", "CO2", "🏆 Best"]].style.format({
        "Cost": "£{:.2f}", "CO2": "{:.1f}", "Energy": "{:.1f}"
    }))

# ================== EMISSIONS EXPLORER ==================
elif page == "Emissions Explorer":
    st.title("🌍 Emissions Explorer")

    regions = {"UK": 250, "Germany": 300, "France": 100, "California": 200, "Texas": 400}
    region = st.selectbox("Select a Region", list(regions.keys()))
    base_emission = regions[region]

    hours = np.arange(24)
    emissions = base_emission + 50 * np.sin((hours - 16) * np.pi / 12) + np.random.normal(0, 10, 24)

    fig, ax = plt.subplots()
    ax.plot(hours, emissions, marker="o")
    ax.set_title(f"Estimated Hourly Emissions for {region}")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("gCO₂/kWh")
    st.pyplot(fig)

# ================== BATTERY SIZING TOOL ==================
elif page == "Battery Sizing Tool":
    st.title("🔧 Battery Sizing Estimator")

    daily_kWh = st.number_input("Estimated Daily Energy Need (kWh)", min_value=1.0, value=20.0)
    days_of_autonomy = st.slider("Days of Backup Required", 1, 7, 2)
    efficiency = st.slider("System Efficiency (%)", 70, 100, 90)

    required_capacity = daily_kWh * days_of_autonomy / (efficiency / 100)
    st.metric("Recommended Battery Capacity", f"{required_capacity:.1f} kWh")
