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
    st.title("🔋 FlexKit Energy Strategy Simulator")
    st.markdown("""
    Welcome to FlexKit's battery dispatch simulator.  
    You can test strategies across carbon, price, and grid demand.
    """)

    st.header("⚙️ Configure your battery simulation here...")
    st.markdown("*(Simulation controls and graphs would be here.)*")

# ================== PAGE: STRATEGY COMPARISON ==================
elif page == "Strategy Comparison":
    st.title("📊 Strategy Comparison")

    st.sidebar.header("⚖️ Scoring Weights")
    cost_weight = st.sidebar.slider("Weight for Cost", 0.0, 1.0, 0.5)
    carbon_weight = 1.0 - cost_weight
    st.sidebar.markdown(f"🔁 Carbon Weight = **{carbon_weight:.2f}**")

    results = [
        {"Strategy": "Blended (Price + Carbon)", "Energy (kWh)": 14.6, "Cost (£)": 9.32, "CO₂ (kg)": 7.1},
        {"Strategy": "Tariff Avoidance Only", "Energy (kWh)": 12.3, "Cost (£)": 6.85, "CO₂ (kg)": 8.5},
        {"Strategy": "Price Arbitrage", "Energy (kWh)": 15.1, "Cost (£)": 11.2, "CO₂ (kg)": 9.9},
        {"Strategy": "Carbon Minimizer", "Energy (kWh)": 13.8, "Cost (£)": 8.90, "CO₂ (kg)": 5.3}
    ]
    df = pd.DataFrame(results)

    df["Score"] = (
        cost_weight * (1 - (df["Cost (£)"] - df["Cost (£)"].min()) / (df["Cost (£)"].max() - df["Cost (£)"].min())) +
        carbon_weight * (1 - (df["CO₂ (kg)"] - df["CO₂ (kg)"].min()) / (df["CO₂ (kg)"].max() - df["CO₂ (kg)"].min()))
    )

    best_idx = df["Score"].idxmax()
    df["🏆 Best"] = ""
    df.loc[best_idx, "🏆 Best"] = "✅"

    st.subheader("🏁 Strategy Ranking")
    st.dataframe(df[["Strategy", "Energy (kWh)", "Cost (£)", "CO₂ (kg)", "🏆 Best"]].style.format({
        "Cost (£)": "£{:.2f}",
        "CO₂ (kg)": "{:.1f}",
        "Energy (kWh)": "{:.1f}"
    }).highlight_max(subset=["Score"], color="lightgreen"))

# ================== PAGE: EMISSIONS EXPLORER ==================
elif page == "Emissions Explorer":
    st.title("🌍 Emissions Explorer")

    regions = {
        "UK": 250, "Germany": 300, "France": 100, "California": 200, "Texas": 400
    }
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

# ================== PAGE: BATTERY SIZING TOOL ==================
elif page == "Battery Sizing Tool":
    st.title("🔧 Battery Sizing Estimator")

    daily_kWh = st.number_input("Estimated Daily Energy Need (kWh)", min_value=1.0, value=20.0)
    days_of_autonomy = st.slider("Days of Backup Required", 1, 7, 2)
    efficiency = st.slider("System Efficiency (%)", 70, 100, 90)

    required_capacity = daily_kWh * days_of_autonomy / (efficiency / 100)
    st.metric("Recommended Battery Capacity", f"{required_capacity:.1f} kWh")
