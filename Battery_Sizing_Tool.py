import streamlit as st

st.set_page_config(page_title="Battery Sizing Tool", layout="wide")
st.title("🔧 Battery Sizing Estimator")

daily_kWh = st.number_input("Estimated Daily Energy Need (kWh)", min_value=1.0, value=20.0)
days_of_autonomy = st.slider("Days of Backup Required", 1, 7, 2)
efficiency = st.slider("System Efficiency (%)", 70, 100, 90)

required_capacity = daily_kWh * days_of_autonomy / (efficiency / 100)

st.metric("Recommended Battery Capacity", f"{required_capacity:.1f} kWh")
