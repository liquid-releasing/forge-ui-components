"""Thin Streamlit render layer for tone selector."""

import streamlit as st

from .core import TONE_CATALOG, ToneSelection


def render_tone_cards(selection: ToneSelection, *, key_prefix: str = "tone") -> ToneSelection:
    """Render the 6 tone cards in a row with selection state.

    Args:
        selection: Current tone selection.
        key_prefix: Unique prefix for Streamlit widget keys.

    Returns:
        Updated ToneSelection.
    """
    cols = st.columns(len(TONE_CATALOG))
    for col, card in zip(cols, TONE_CATALOG):
        with col:
            selected = selection.tone_key == card.key
            border = "border: 2px solid #4C8BF5;" if selected else "border: 1px solid #ddd;"
            st.markdown(
                f'<div style="padding: 8px; border-radius: 8px; {border} text-align: center;">'
                f"<strong>{card.title}</strong></div>",
                unsafe_allow_html=True,
            )
            if st.button("Select", key=f"{key_prefix}_{card.key}", use_container_width=True):
                selection.tone_key = card.key
                selection.slider_values = {
                    s["key"]: s["default"] for s in card.sliders
                }

    return selection


def render_tone_sliders(selection: ToneSelection, *, key_prefix: str = "tone") -> ToneSelection:
    """Render sliders for the currently selected tone.

    Args:
        selection: Current tone selection.
        key_prefix: Unique prefix for Streamlit widget keys.

    Returns:
        Updated ToneSelection with slider values.
    """
    card = selection.selected_card
    if card is None:
        return selection

    # Impact slider
    selection.impact = st.slider(
        "Impact",
        min_value=0.0,
        max_value=1.0,
        value=selection.impact,
        step=0.05,
        key=f"{key_prefix}_impact",
    )

    # Tone-specific sliders
    for slider in card.sliders:
        val = st.slider(
            slider["label"],
            min_value=slider["min"],
            max_value=slider["max"],
            value=selection.slider_values.get(slider["key"], slider["default"]),
            step=slider["step"],
            key=f"{key_prefix}_{slider['key']}",
        )
        selection.slider_values[slider["key"]] = val

    return selection
