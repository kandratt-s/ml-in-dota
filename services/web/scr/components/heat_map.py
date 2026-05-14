import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import time
from datetime import datetime
from scr.infra.config import settings
from scr.api.heatmap_client import get_inference_client


def build_figure(matrix, max_value=None):
    """Build a Plotly figure with heatmap overlay on the Dota 2 map."""
    fig = go.Figure()

    try:
        img = Image.open(settings.MAP_PATH)
    except FileNotFoundError:
        st.error(f"Map file not found: {settings.MAP_PATH}")
        return fig

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

    z_data = matrix if matrix else [[0] * settings.CELLS for _ in range(settings.CELLS)]
    
    if max_value is None:
        flat_list = [item for sublist in z_data for item in sublist]
        max_value = max(flat_list) if any(flat_list) else 1.0

    fig.add_trace(
        go.Heatmap(
            z=z_data,
            zmin=0,
            zmax=max_value,
            colorscale=[
                [0.0, "rgba(255, 0, 0, 0.0)"],
                [0.2, "rgba(255, 0, 0, 0.2)"],
                [0.5, "rgba(255, 0, 0, 0.5)"],
                [1.0, "rgba(255, 0, 0, 0.9)"],
            ],
            zsmooth='best',
            showscale=True,
            hoverinfo="z",
            connectgaps=True
        )
    )

    fig.update_xaxes(range=[0, settings.CELLS], visible=False)
    fig.update_yaxes(range=[0, settings.CELLS], visible=False, scaleanchor="x")

    fig.update_layout(
        height=800,
        margin=dict(l=0, r=0, t=0, b=0),
        modebar_remove=['zoom', 'pan', 'select', 'lasso2d']
    )

    return fig


def render_heatmap():
    """Render the heatmap visualization with controls."""
    client = get_inference_client()
    
    # Create columns for controls
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        is_live = st.toggle("Live Mode (Auto-refresh)", value=True)
    
    with col2:
        if is_live:
            refresh_rate = st.slider(
                "Update interval (sec)",
                min_value=settings.REFRESH_INTERVAL_SECONDS,
                max_value=settings.MAX_REFRESH_RATE_SECONDS,
                value=1.0,
                step=0.5,
            )
        else:
            refresh_rate = None
    
    with col3:
        if st.button("Check Service Health"):
            health = client.check_inference_health()
            if health:
                st.success("Inference service is healthy")
                st.json(health)
            else:
                st.warning("Could not reach inference service")

    # Create containers for display
    placeholder = st.empty()
    status_placeholder = st.empty()

    # Initial load
    matrix = client.get_current_heatmap()
    
    with placeholder.container():
        if matrix:
            fig = build_figure(matrix)
            st.plotly_chart(fig, width="stretch")
            status_placeholder.success(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.info("Waiting for heatmap data from inference service...")
            fig = build_figure(None)
            st.plotly_chart(fig, width="stretch")

    # If live mode enabled, use Streamlit's rerun with interval
    if is_live:
        st.session_state.setdefault("last_update", None)
        current_time = datetime.now()
        
        # Use the refresh_rate for display purposes
        # Streamlit will handle the actual rerun cycle
        if refresh_rate:
            # Use st.empty() and time.sleep patterns are not recommended
            # Instead, rely on Streamlit's native auto-rerun features
            # or use a library like streamlit-autorefresh
            pass
            
        time.sleep(refresh_rate)
        if is_live:
            st.rerun()