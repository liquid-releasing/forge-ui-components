"""Thin Streamlit render layer for beat bar."""

import streamlit as st

from .core import BeatData


def render_beat_bar(beat_data: BeatData | None, *, key: str = "beat_bar"):
    """Render beat visualization and stats.

    Args:
        beat_data: Beat detection results, or None if not yet generated.
        key: Unique Streamlit widget key.
    """
    if beat_data is None:
        st.info("No beat data. Run beat detection to visualize.")
        return

    st.caption(f"BPM: {beat_data.bpm:.1f} — {len(beat_data.beat_times)} beats detected")

    # Beat markers as a simple bar chart
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=beat_data.beat_times,
        y=[1] * len(beat_data.beat_times),
        width=0.05,
        marker_color="#4C8BF5",
        showlegend=False,
    ))
    fig.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=0, b=20),
        xaxis_title="Time (s)",
        yaxis=dict(visible=False),
        bargap=0,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
