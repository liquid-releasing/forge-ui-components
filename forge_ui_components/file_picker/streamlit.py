"""Thin Streamlit render layer for file picker."""

import streamlit as st

from .core import FilePickerState, compute_file_stats


def render_file_picker(state: FilePickerState, *, key: str) -> FilePickerState:
    """Render a file picker with upload, clear button, and stats display.

    Args:
        state: Current picker state.
        key: Unique Streamlit widget key.

    Returns:
        Updated FilePickerState.
    """
    col1, col2 = st.columns([5, 1])

    with col1:
        uploaded = st.file_uploader(
            state.label,
            type=state.accepted_extensions or None,
            key=f"{key}_uploader",
        )

    with col2:
        if state.has_file:
            st.write("")  # spacer
            if st.button("✕", key=f"{key}_clear", help="Clear file"):
                state.clear()
                return state

    if uploaded is not None and uploaded.name != state.file_name:
        state.file_data = uploaded.getvalue()
        state.file_name = uploaded.name
        state.stats = compute_file_stats(uploaded.name, state.file_data)

    if state.stats:
        st.caption(f"{state.stats['name']} — {state.stats['size_kb']} KB")

    return state
