
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

st.set_page_config(page_title="FlexKit Animated Dispatch", layout="wide")
st.title("FlexKit Dispatch Animation Demo")

# --- Settings ---
battery_kWh = st.sidebar.slider("Battery Capacity (kWh)", 5, 50, 20)
power_kW = st.sidebar.slider("Power Rating (kW)", 1, 10, 5)
soc_start = st.sidebar.slider("Starting SOC", 0.0, 1.0, 0.5, 0.01)
duration_hours = 1  # Simulating 1 hour in seconds (3600 steps)

st.sidebar.markdown("Simulating 1 hour with second-by-second granularity.")

# --- Synthetic signal data ---
np.random.seed(42)
seconds = np.arange(0, duration_hours * 3600)
price = 100 + 30 * np.sin(2 * np.pi * seconds / 3600)
carbon = 250 + 40 * np.cos(2 * np.pi * seconds / 3600)
demand = 2 + 0.5 * np.sin(2 * np.pi * seconds / 3600)

# --- Dispatch logic ---
soc = soc_start
soc_series = []
actions = []
for t in range(len(seconds)):
    p, c = price[t], carbon[t]
    action = "idle"
    if p < 100 and soc < 1.0:
        action = "charge"
        soc += power_kW / battery_kWh / 3600
    elif p > 130 and soc > 0.2:
        action = "discharge"
        soc -= power_kW / battery_kWh / 3600
    soc = np.clip(soc, 0.0, 1.0)
    soc_series.append(soc)
    actions.append(action)

df = pd.DataFrame({
    "Second": seconds,
    "Price": price,
    "Carbon": carbon,
    "SOC": soc_series,
    "Action": actions
})

# --- Animation ---
st.subheader("SOC Animation Over 1 Hour")

fig, ax = plt.subplots(figsize=(8, 4))
line, = ax.plot([], [], lw=2)
ax.set_xlim(0, len(seconds))
ax.set_ylim(0, 1)
ax.set_xlabel("Seconds")
ax.set_ylabel("State of Charge")

def init():
    line.set_data([], [])
    return line,

def update(frame):
    x = df["Second"][:frame]
    y = df["SOC"][:frame]
    line.set_data(x, y)
    return line,

ani = animation.FuncAnimation(fig, update, frames=len(seconds), init_func=init, blit=True, interval=1)

from streamlit.components.v1 import html
import base64
from io import BytesIO

# Convert to HTML5 video
video_buf = BytesIO()
ani.save(video_buf, writer="ffmpeg", fps=30)
video_encoded = base64.b64encode(video_buf.getvalue()).decode("utf-8")
video_html = f'<video width="700" controls autoplay loop><source src="data:video/mp4;base64,{video_encoded}" type="video/mp4"></video>'

html(video_html, height=400)
