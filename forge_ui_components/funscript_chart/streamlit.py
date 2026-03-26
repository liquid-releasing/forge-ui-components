"""Thin Streamlit render layer for funscript charts."""

from __future__ import annotations

import streamlit as st

from .core import (
    MONO_BLUE,
    AnnotationBand,
    PointSeries,
    monochrome_figure,
    prepare_chart_data,
    vibrant_figure,
)


def render_monochrome(
    actions: list[dict],
    *,
    color: str = MONO_BLUE,
    height: int = 180,
    show_axes: bool = True,
    line_width: float = 1.5,
    caption: str = "",
    key: str | None = None,
):
    """Render a monochrome funscript chart in Streamlit.

    Drop-in replacement for _funscript_chart (project_tab),
    _plot_device (device_tab), _plot_funscript (tone_tab).
    """
    data = prepare_chart_data(actions)
    if not data["times_s"]:
        return
    fig = monochrome_figure(
        data["times_s"],
        data["positions"],
        color=color,
        height=height,
        show_axes=show_axes,
        line_width=line_width,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
    if caption:
        st.caption(caption)


def render_monochrome_from_arrays(
    times_s: list[float],
    positions: list[float],
    *,
    color: str = MONO_BLUE,
    height: int = 150,
    show_axes: bool = False,
    line_width: float = 1.0,
    key: str | None = None,
):
    """Render a monochrome chart from pre-extracted arrays.

    Used by device_tab and tone_tab where times_s/positions are already computed.
    """
    if not times_s:
        return
    fig = monochrome_figure(
        times_s,
        positions,
        color=color,
        height=height,
        show_axes=show_axes,
        line_width=line_width,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_vibrant(
    series: PointSeries,
    bands: list[AnnotationBand],
    *,
    view_state=None,
    color_mode: str = "velocity",
    height: int = 300,
    duration_ms: int = 0,
    key: str = "chart",
    selection_mode: list[str] | None = None,
):
    """Render a color-coded funscript chart with phrase annotations.

    Drop-in replacement for FunscriptChart.render_streamlit().

    Returns the Plotly event dict (may be None or empty).
    """
    fig = vibrant_figure(
        series,
        bands,
        view_state=view_state,
        color_mode=color_mode,
        height=height,
        duration_ms=duration_ms,
    )
    if selection_mode is None:
        selection_mode = ["points", "box"]
    event = st.plotly_chart(
        fig,
        key=key,
        on_select="rerun",
        selection_mode=selection_mode,
    )
    return event


def render_static(
    actions: list[dict],
    bands: list[AnnotationBand] | None = None,
    *,
    color_mode: str = "velocity",
    height_px: int = 250,
    width_px: int = 1400,
    show_labels: bool = True,
    title: str = "",
    caption: str = "",
    key: str | None = None,
):
    """Render a static PNG funscript chart in Streamlit.

    Fast, non-interactive. Use for overviews and previews.
    Color shows velocity (blue=slow → red=fast) with phrase boundaries.
    """
    from .static import render_vibrant_static, render_monochrome_static

    if not actions:
        return

    if color_mode == "velocity" or color_mode == "vibrant":
        png = render_vibrant_static(
            actions, bands,
            height_px=height_px, width_px=width_px,
            show_labels=show_labels, title=title,
        )
    else:
        times_s = [a["at"] / 1000.0 for a in actions]
        positions = [a["pos"] for a in actions]
        png = render_monochrome_static(
            times_s, positions,
            height_px=height_px, width_px=width_px, title=title,
        )

    st.image(png, use_container_width=True)
    if caption:
        st.caption(caption)


def render_static_from_arrays(
    times_s: list[float],
    positions: list[float],
    *,
    color_mode: str = "monochrome",
    height_px: int = 180,
    width_px: int = 1400,
    title: str = "",
    caption: str = "",
):
    """Render a static PNG chart from pre-extracted arrays.

    Used by device_tab and tone_tab for before/after previews.
    """
    if not times_s:
        return

    from .static import render_monochrome_static, render_vibrant_static
    from .core import PointSeries, compute_chart_data

    if color_mode == "monochrome":
        png = render_monochrome_static(
            times_s, positions,
            height_px=height_px, width_px=width_px, title=title,
        )
    else:
        # Build actions for compute_chart_data
        actions = [{"at": int(t * 1000), "pos": int(p)} for t, p in zip(times_s, positions)]
        png = render_vibrant_static(
            actions, height_px=height_px, width_px=width_px, title=title,
        )

    st.image(png, use_container_width=True)
    if caption:
        st.caption(caption)


def render_stats_row(stats: dict):
    """Render funscript stats as a Streamlit metric row.

    Args:
        stats: Output of funscript_stats().
    """
    if not stats:
        return
    cols = st.columns(5)
    cols[0].metric("Duration", stats["duration_fmt"])
    cols[1].metric("Actions", f"{stats['action_count']:,}")
    cols[2].metric("Avg speed", f"{stats['avg_speed']:.0f}")
    cols[3].metric("Min pos", stats["min_pos"])
    cols[4].metric("Max pos", stats["max_pos"])
