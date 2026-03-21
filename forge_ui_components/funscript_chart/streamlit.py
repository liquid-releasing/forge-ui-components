"""Thin Streamlit render layer for funscript charts."""

import streamlit as st

from .core import prepare_chart_data, monochrome_figure, vibrant_figure


def render_monochrome(actions: list[dict], *, title: str = "", key: str | None = None):
    """Render a monochrome funscript chart in Streamlit."""
    data = prepare_chart_data(actions)
    fig = monochrome_figure(data, title=title)
    st.plotly_chart(fig, use_container_width=True, key=key)


def render_vibrant(actions: list[dict], phrases: list[dict], *, title: str = "", key: str | None = None):
    """Render a color-coded funscript chart in Streamlit."""
    data = prepare_chart_data(actions)
    fig = vibrant_figure(data, phrases, title=title)
    st.plotly_chart(fig, use_container_width=True, key=key)
