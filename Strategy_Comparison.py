import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Compare Strategies", layout="wide")
st.title("📊 FlexKit Strategy Comparison")

results = [
    {"Strategy": "Blended (Price + Carbon)", "Energy (kWh)": 14.6, "Cost (£)": 9.32, "CO₂ (kg)": 7.1},
    {"Strategy": "Tariff Avoidance Only", "Energy (kWh)": 12.3, "Cost (£)": 6.85, "CO₂ (kg)": 8.5},
    {"Strategy": "Price Arbitrage", "Energy (kWh)": 15.1, "Cost (£)": 11.2, "CO₂ (kg)": 9.9},
    {"Strategy": "Carbon Minimizer", "Energy (kWh)": 13.8, "Cost (£)": 8.90, "CO₂ (kg)": 5.3}
]
df = pd.DataFrame(results)

st.sidebar.header("⚖️ Scoring Weights")
cost_weight = st.sidebar.slider("Weight for Cost", 0.0, 1.0, 0.5)
carbon_weight = 1.0 - cost_weight
st.sidebar.markdown(f"🔁 Carbon Weight = **{carbon_weight:.2f}**")

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
