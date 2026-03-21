"""Thin Streamlit render layer for beat bar."""

from __future__ import annotations

import streamlit as st

from .core import beat_bar_figure, beat_stats


def render_beat_bar(beat_map, *, height: int = 80, show_energy: bool = True, key: str = "beat_bar"):
    """Render beat visualization from a videoflow AudioBeatMap.

    Args:
        beat_map: videoflow.audio.AudioBeatMap instance, or None.
        height: Chart height in pixels.
        show_energy: If True, bar height reflects per-beat energy.
        key: Unique Streamlit widget key.
    """
    if beat_map is None:
        st.info("No beat data. Run beat detection to visualize.")
        return

    stats = beat_stats(beat_map)
    st.caption(
        f"BPM: **{stats['bpm']:.1f}** · "
        f"{stats['beat_count']} beats · "
        f"{stats['downbeat_count']} downbeats · "
        f"{stats['phrase_count']} phrases"
    )

    energy = beat_map.energy if show_energy else None
    fig = beat_bar_figure(
        beat_map.beats,
        energy=energy,
        duration_ms=beat_map.duration_ms,
        height=height,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_beat_stats_row(beat_map):
    """Render beat stats as a Streamlit metric row.

    Args:
        beat_map: videoflow.audio.AudioBeatMap instance.
    """
    if beat_map is None:
        return
    stats = beat_stats(beat_map)
    cols = st.columns(4)
    cols[0].metric("BPM", f"{stats['bpm']:.1f}")
    cols[1].metric("Beats", f"{stats['beat_count']:,}")
    cols[2].metric("Downbeats", f"{stats['downbeat_count']:,}")
    cols[3].metric("Phrases", f"{stats['phrase_count']:,}")
