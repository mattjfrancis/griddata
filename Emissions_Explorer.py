import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Emissions Explorer", layout="wide")
st.title("🌍 Grid Emissions Explorer")

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
