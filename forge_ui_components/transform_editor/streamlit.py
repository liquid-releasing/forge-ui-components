"""Thin Streamlit render layer for transform editor."""

import streamlit as st

from .core import TransformConfig


def render_sliders(config: TransformConfig, *, key_prefix: str) -> TransformConfig:
    """Render slider controls for a transform config.

    Args:
        config: Transform configuration with slider definitions.
        key_prefix: Unique prefix for Streamlit widget keys.

    Returns:
        Updated TransformConfig with current slider values.
    """
    for slider in config.sliders:
        val = st.slider(
            slider["label"],
            min_value=slider["min"],
            max_value=slider["max"],
            value=config.get_value(slider["key"]),
            step=slider["step"],
            key=f"{key_prefix}_{slider['key']}",
        )
        config.set_value(slider["key"], val)
    return config


def render_accept_cancel(*, key_prefix: str) -> str | None:
    """Render Accept / Cancel buttons.

    Returns:
        "accept", "cancel", or None if neither pressed.
    """
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Accept", key=f"{key_prefix}_accept", type="primary"):
            return "accept"
    with col2:
        if st.button("Cancel", key=f"{key_prefix}_cancel"):
            return "cancel"
    return None
