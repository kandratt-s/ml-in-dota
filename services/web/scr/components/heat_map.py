import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import time
from datetime import datetime

from scr.infra.config import settings
from scr.api.heatmap_client import get_heatmap_client


def build_figure(matrix, max_value=None):
    fig = go.Figure()

    try:
        img = Image.open(settings.MAP_PATH)
    except FileNotFoundError:
        st.error(f"Файл карты не найден: {settings.MAP_PATH}")
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
            # Настройка: только красный разной насыщенности
            colorscale=[
                [0.0, "rgba(255, 0, 0, 0.0)"],  # 0 - полностью прозрачный
                [0.2, "rgba(255, 0, 0, 0.2)"],  # Слабо-розовый/прозрачный
                [0.5, "rgba(255, 0, 0, 0.5)"],  # Полупрозрачный красный
                [1.0, "rgba(255, 0, 0, 0.9)"],  # Насыщенный красный
            ],
            # ВКЛЮЧАЕМ СГЛАЖИВАНИЕ ДЛЯ РЕАЛИЗМА
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
        # Убираем лишние элементы управления Plotly для чистоты
        modebar_remove=['zoom', 'pan', 'select', 'lasso2d']
    )

    return fig


def render_heatmap():
    client = get_heatmap_client()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        is_live = st.toggle("Live Mode (Auto-refresh)", value=True)
    with col2:
        refresh_rate = st.slider("Update interval (sec)", 0.5, 5.0, 1.0)

    placeholder = st.empty()
    status_text = st.empty()

    while True:
        matrix = client.get_current_heatmap()
        
        with placeholder.container():
            if matrix:
                fig = build_figure(matrix)
                st.plotly_chart(fig, use_container_width=True, key=f"map_{datetime.now().timestamp()}")
                status_text.success(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
            else:
                st.info("Waiting for data from Redis (key: 'heat_map')...")
                fig = build_figure(None)
                st.plotly_chart(fig, use_container_width=True)

        if not is_live:
            break
            
        time.sleep(refresh_rate)
        if is_live:
            st.rerun()