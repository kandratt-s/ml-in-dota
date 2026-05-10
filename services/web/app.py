import streamlit as st
from scr.components.heat_map import render_heatmap

st.set_page_config(
    page_title="Dota2 Heatmap Tracker",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("Dota 2d")

render_heatmap()