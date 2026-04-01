import streamlit as st
import plotly.graph_objects as go
import random
from datetime import datetime
from PIL import Image

from scr.infra.config import settings

# -------------------------
# FAKE DATA GENERATION
# -------------------------
def generate_fake_heatmap():
    heat = [
        [random.random() for _ in range(settings.CELLS)]
        for _ in range(settings.CELLS)
    ]

    return {
        "heat": heat,
        "max_value": 1.0,
        "updated_at": datetime.now(),
    }


# -------------------------
# PLOTLY FIGURE
# -------------------------
def build_figure(data):
    fig = go.Figure()

    img = Image.open(settings.MAP_PATH)
    # фон — карта
    fig.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=0,
            y=settings.CELLS,
            sizex=settings.CELLS,
            sizey=settings.CELLS,
            sizing="stretch",
            layer="below"
        )
    )

    # heatmap overlay
    fig.add_trace(
        go.Heatmap(
            z=data["heat"],
            zmin=0,

            zmax=data["max_value"],
            colorscale=[
                [0.0, "rgba(255,0,0,0.0)"],
                [0.3, "rgba(255,100,0,0.3)"],
                [0.6, "rgba(255,200,0,0.6)"],
                [1.0, "rgba(255,0,0,0.9)"],
            ],
            showscale=True,
        )
    )

    fig.update_xaxes(
        range=[0, settings.CELLS],
        showgrid=True,
        dtick=1,
        visible=False,
    )

    fig.update_yaxes(
        range=[0, settings.CELLS],
        showgrid=True,
        dtick=1,
        visible=False,
        scaleanchor="x",
    )

    fig.update_layout(
        height=800,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig


# -------------------------
# UI
# -------------------------
def render_heatmap():
    st.subheader("Heatmap (mock)")

    # имитация состояния
    active = st.session_state.get("session_active", False)

    st.write("Session:", "🟢 Active" if active else "🔴 Inactive")

    # if not active:
    #     st.info("Session inactive")
    #     return

    data = generate_fake_heatmap()

    fig = build_figure(data)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Updated: {data['updated_at']}")