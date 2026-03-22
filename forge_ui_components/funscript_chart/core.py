"""Framework-agnostic funscript chart logic.

Two chart modes:
- Monochrome: single-color line, fast, no assessment needed.
  Used on Project tab (load preview), Device tab (before/after), Tone tab (before/after).
- Vibrant: color-coded by velocity or amplitude, with phrase annotation boxes.
  Used in Phrase selector, post-assessment views.

Data pipeline:
  actions → prepare_chart_data() → monochrome_figure()
  actions → compute_chart_data() → FunscriptChart → vibrant figure

Colour modes (vibrant):
  velocity: blue (slow) → cyan → green → yellow → red (fast)
  amplitude: dark blue (low) → purple → magenta → bright (high)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import List, Tuple

import plotly.graph_objects as go


# ── Constants ────────────────────────────────────────────────────────────────

MONO_BLUE = "#4C8BF5"

# Velocity colour stops: blue (slow) -> cyan -> green -> yellow -> red (fast)
_VELOCITY_STOPS: List[Tuple[float, str]] = [
    (0.0, "#1a2fff"),
    (0.25, "#00bfff"),
    (0.5, "#00e000"),
    (0.75, "#ffdd00"),
    (1.0, "#ff1a1a"),
]

# Amplitude colour stops: dark blue (low) -> purple -> magenta -> bright (high)
_AMPLITUDE_STOPS: List[Tuple[float, str]] = [
    (0.0, "#0d0d2b"),
    (0.33, "#4b0082"),
    (0.66, "#c71585"),
    (1.0, "#ff69b4"),
]

# Assessment type colours for annotation bands
ANNOTATION_COLORS = {
    "phase": "rgba(100, 149, 237, 0.25)",
    "cycle": "rgba(60, 179, 113, 0.25)",
    "pattern": "rgba(255, 165, 0, 0.25)",
    "phrase": "rgba(255, 255, 255, 0.15)",
    "transition": "rgba(255, 99, 71, 0.60)",
}

# Funscripts with more total actions than this use fast grey-line rendering
_LARGE_FUNSCRIPT_THRESHOLD = 2500
_MAX_SEGMENT_TRACES = 600


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class PointSeries:
    """Pre-computed display data for a single funscript channel."""

    times_ms: List[int] = field(default_factory=list)
    positions: List[float] = field(default_factory=list)
    velocities: List[float] = field(default_factory=list)
    velocity_norm: List[float] = field(default_factory=list)
    amplitude_norm: List[float] = field(default_factory=list)
    colors_velocity: List[str] = field(default_factory=list)
    colors_amplitude: List[str] = field(default_factory=list)


@dataclass
class AnnotationBand:
    """A coloured background band or marker for one assessment item."""

    kind: str
    start_ms: int
    end_ms: int
    label: str
    color: str
    row: int = 0
    name: str = ""


# ── Monochrome chart (simple, fast) ─────────────────────────────────────────


def prepare_chart_data(actions: list[dict]) -> dict:
    """Extract timestamps and positions from funscript actions.

    Args:
        actions: List of {"at": ms, "pos": 0-100} dicts.

    Returns:
        Dict with "times_s" (seconds) and "positions" lists.
    """
    if not actions:
        return {"times_s": [], "positions": []}
    times_s = [a["at"] / 1000.0 for a in actions]
    positions = [a["pos"] for a in actions]
    return {"times_s": times_s, "positions": positions}


def monochrome_figure(
    times_s: list[float],
    positions: list[float],
    *,
    color: str = MONO_BLUE,
    height: int = 180,
    show_axes: bool = True,
    line_width: float = 1.5,
) -> go.Figure:
    """Build a monochrome Plotly figure — fast, no assessment needed.

    Replaces _funscript_chart (project_tab), _plot_device (device_tab),
    _plot_funscript (tone_tab).

    Args:
        times_s: Timestamps in seconds.
        positions: Position values (0-100).
        color: Line color.
        height: Chart height in pixels.
        show_axes: Show axis labels and tick marks (False for compact previews).
        line_width: Line width.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times_s,
        y=positions,
        mode="lines",
        line=dict(color=color, width=line_width),
        showlegend=False,
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            title="time (s)" if show_axes else None,
            showgrid=False,
            showticklabels=show_axes,
        ),
        yaxis=dict(
            title="pos" if show_axes else None,
            range=[0, 100],
            showgrid=False,
            showticklabels=show_axes,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.05)",
        showlegend=False,
    )
    return fig


# ── Vibrant chart data computation ───────────────────────────────────────────


def compute_chart_data(actions: list[dict]) -> PointSeries:
    """Compute all display data for a list of funscript actions.

    Args:
        actions: List of {"at": int, "pos": int} dicts.

    Returns:
        PointSeries with all fields populated.
    """
    if not actions:
        return PointSeries()

    times = [a["at"] for a in actions]
    pos = [float(a["pos"]) for a in actions]
    n = len(actions)

    # Velocity: forward difference, first point copies second
    vels: list[float] = [0.0] * n
    for i in range(1, n):
        dt = max(1, times[i] - times[i - 1])
        vels[i] = abs(pos[i] - pos[i - 1]) / dt
    vels[0] = vels[1] if n > 1 else 0.0

    max_vel = max(vels) if max(vels) > 0 else 1.0
    vel_norm = [v / max_vel for v in vels]
    amp_norm = [p / 100.0 for p in pos]

    col_vel = [_interpolate_color(_VELOCITY_STOPS, v) for v in vel_norm]
    col_amp = [_interpolate_color(_AMPLITUDE_STOPS, a) for a in amp_norm]

    return PointSeries(
        times_ms=times,
        positions=pos,
        velocities=vels,
        velocity_norm=vel_norm,
        amplitude_norm=amp_norm,
        colors_velocity=col_vel,
        colors_amplitude=col_amp,
    )


def compute_annotation_bands(assessment_dict: dict) -> list[AnnotationBand]:
    """Build annotation bands from an assessment to_dict() result."""
    bands: list[AnnotationBand] = []
    row_map = {"phase": 0, "cycle": 1, "pattern": 2, "phrase": 3, "transition": 4}

    for ph in assessment_dict.get("phases", []):
        bands.append(AnnotationBand(
            kind="phase",
            start_ms=ph["start_ms"], end_ms=ph["end_ms"],
            label=f"Phase: {ph.get('label', '')}",
            color=ANNOTATION_COLORS["phase"],
            row=row_map["phase"],
        ))

    for cy in assessment_dict.get("cycles", []):
        bands.append(AnnotationBand(
            kind="cycle",
            start_ms=cy["start_ms"], end_ms=cy["end_ms"],
            label=f"Cycle: {cy.get('label', '')}",
            color=ANNOTATION_COLORS["cycle"],
            row=row_map["cycle"],
        ))

    for pt in assessment_dict.get("patterns", []):
        for cy in pt.get("cycles", []):
            bands.append(AnnotationBand(
                kind="pattern",
                start_ms=cy["start_ms"], end_ms=cy["end_ms"],
                label=f"Pattern: {pt.get('pattern_label', '')}",
                color=ANNOTATION_COLORS["pattern"],
                row=row_map["pattern"],
            ))

    for i, ph in enumerate(assessment_dict.get("phrases", [])):
        bands.append(AnnotationBand(
            kind="phrase",
            start_ms=ph["start_ms"], end_ms=ph["end_ms"],
            label=f"Phrase ({ph.get('bpm', 0):.0f} BPM): {ph.get('pattern_label', '')}",
            color=ANNOTATION_COLORS["phrase"],
            row=row_map["phrase"],
            name=f"P{i + 1}",
        ))

    for tr in assessment_dict.get("bpm_transitions", []):
        ms = tr["at_ms"]
        bands.append(AnnotationBand(
            kind="transition",
            start_ms=ms, end_ms=ms,
            label=f"BPM transition: {tr.get('from_bpm', 0):.0f} -> {tr.get('to_bpm', 0):.0f}",
            color=ANNOTATION_COLORS["transition"],
            row=row_map["transition"],
        ))

    return bands


def slice_series(series: PointSeries, start_ms: int, end_ms: int) -> PointSeries:
    """Return a new PointSeries containing only points within [start_ms, end_ms]."""
    indices = [
        i for i, t in enumerate(series.times_ms)
        if start_ms <= t <= end_ms
    ]
    if not indices:
        return PointSeries()
    return PointSeries(
        times_ms=[series.times_ms[i] for i in indices],
        positions=[series.positions[i] for i in indices],
        velocities=[series.velocities[i] for i in indices],
        velocity_norm=[series.velocity_norm[i] for i in indices],
        amplitude_norm=[series.amplitude_norm[i] for i in indices],
        colors_velocity=[series.colors_velocity[i] for i in indices],
        colors_amplitude=[series.colors_amplitude[i] for i in indices],
    )


def slice_bands(bands: list[AnnotationBand], start_ms: int, end_ms: int) -> list[AnnotationBand]:
    """Return bands that overlap [start_ms, end_ms]."""
    return [b for b in bands if b.end_ms >= start_ms and b.start_ms <= end_ms]


# ── Vibrant figure builder ───────────────────────────────────────────────────


def vibrant_figure(
    series: PointSeries,
    bands: list[AnnotationBand],
    *,
    view_state=None,
    color_mode: str = "velocity",
    height: int = 300,
    large_funscript_threshold: int = _LARGE_FUNSCRIPT_THRESHOLD,
    duration_ms: int = 0,
) -> go.Figure:
    """Build a color-coded Plotly figure with phrase annotation boxes.

    Args:
        series: Pre-computed PointSeries.
        bands: Annotation bands (phrase boxes, transitions, etc).
        view_state: Optional object with .has_zoom(), .has_selection(), zoom/selection attrs.
        color_mode: "velocity" or "amplitude".
        height: Chart height in pixels.
        large_funscript_threshold: Action count above which fast grey-line rendering is used.
        duration_ms: Full funscript duration for default x-axis range.

    Returns:
        plotly.graph_objects.Figure
    """
    full_start = series.times_ms[0] if series.times_ms else 0
    full_end = series.times_ms[-1] if series.times_ms else duration_ms

    # Zoom support
    has_zoom = view_state is not None and hasattr(view_state, "has_zoom") and view_state.has_zoom()
    has_selection = view_state is not None and hasattr(view_state, "has_selection") and view_state.has_selection()

    if has_zoom:
        x_start = view_state.zoom_start_ms
        x_end = view_state.zoom_end_ms
        s = slice_series(series, x_start, x_end)
        visible_bands = slice_bands(bands, x_start, x_end)
    else:
        x_start = full_start
        x_end = full_end
        s = series
        visible_bands = bands

    colors = s.colors_velocity if color_mode == "velocity" else s.colors_amplitude

    fig = go.Figure()

    # --- Phrase bounding boxes ---
    for band in visible_bands:
        if band.kind != "phrase":
            continue
        is_selected = (
            has_selection
            and view_state.selection_start_ms == band.start_ms
            and view_state.selection_end_ms == band.end_ms
        )
        if is_selected:
            border = "rgba(255,220,50,1.0)"
            fill = "rgba(255,220,50,0.15)"
        elif has_selection:
            border = "rgba(255,255,255,0.30)"
            fill = "rgba(60,60,80,0.45)"
        else:
            border = "rgba(255,255,255,0.70)"
            fill = "rgba(255,255,255,0.06)"
        fig.add_vrect(
            x0=band.start_ms, x1=band.end_ms,
            fillcolor=fill,
            line_width=2, line_color=border,
            layer="below",
        )
        if band.name:
            fig.add_annotation(
                x=band.start_ms, y=97,
                text=band.name,
                showarrow=False,
                xanchor="left", yanchor="top",
                font=dict(size=11, color="rgba(255,255,255,0.90)"),
                bgcolor="rgba(0,0,0,0.6)",
            )

    # --- Invisible phrase hit targets ---
    _HIT_STEP_MS = 1_000
    _HIT_Y_LEVELS = [20, 50, 80]
    for band in visible_bands:
        if band.kind != "phrase":
            continue
        xs = list(range(band.start_ms, band.end_ms + _HIT_STEP_MS, _HIT_STEP_MS))
        hit_x = xs * len(_HIT_Y_LEVELS)
        hit_y = [y for y in _HIT_Y_LEVELS for _ in xs]
        fig.add_trace(go.Scatter(
            x=hit_x, y=hit_y,
            mode="markers",
            marker=dict(color="rgba(0,0,0,0)", size=18, line=dict(width=0)),
            hoverinfo="skip",
            showlegend=False,
        ))

    # --- Motion line + dots ---
    n = len(s.times_ms)
    dot_size = 5 if (n - 1) <= _MAX_SEGMENT_TRACES else 3
    large = len(series.times_ms) > large_funscript_threshold

    if n > 0:
        if large:
            fig.add_trace(go.Scatter(
                x=s.times_ms, y=s.positions,
                mode="lines",
                line=dict(color="rgba(200,200,200,0.55)", width=1),
                showlegend=False, hoverinfo="skip",
            ))
            if has_selection:
                sel_s = slice_series(s, view_state.selection_start_ms, view_state.selection_end_ms)
                sel_colors = sel_s.colors_velocity if color_mode == "velocity" else sel_s.colors_amplitude
                for i in range(len(sel_s.times_ms) - 1):
                    fig.add_trace(go.Scatter(
                        x=[sel_s.times_ms[i], sel_s.times_ms[i + 1]],
                        y=[sel_s.positions[i], sel_s.positions[i + 1]],
                        mode="lines",
                        line=dict(color=sel_colors[i], width=2),
                        showlegend=False, hoverinfo="skip",
                    ))
        else:
            for i in range(n - 1):
                fig.add_trace(go.Scatter(
                    x=[s.times_ms[i], s.times_ms[i + 1]],
                    y=[s.positions[i], s.positions[i + 1]],
                    mode="lines",
                    line=dict(color=colors[i], width=2),
                    showlegend=False, hoverinfo="skip",
                ))
        fig.add_trace(go.Scatter(
            x=s.times_ms, y=s.positions,
            mode="markers",
            marker=dict(color=colors, size=dot_size, line=dict(width=0)),
            hovertemplate="t=%{x} ms  pos=%{y}<extra></extra>",
            showlegend=False,
        ))

    # --- Layout ---
    tickvals, ticktext = _compute_ticks(x_start, x_end)
    tickangle = -45 if (x_end - x_start) > 900_000 else 0
    bottom_margin = 60 if tickangle else 30

    fig.update_layout(
        title="",
        height=height,
        margin=dict(l=45, r=10, t=10, b=bottom_margin),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1d23",
        font=dict(color="#cccccc"),
        xaxis=dict(
            title=None,
            range=[x_start, x_end],
            color="#aaaaaa",
            showgrid=False,
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=tickangle,
            fixedrange=True,
        ),
        yaxis=dict(
            title="pos",
            range=[0, 100],
            color="#aaaaaa",
            showgrid=False,
            fixedrange=True,
        ),
        showlegend=False,
        dragmode=False,
    )

    return fig


# ── Funscript stats ──────────────────────────────────────────────────────────


def funscript_stats(actions: list[dict]) -> dict:
    """Compute display stats for funscript actions.

    Args:
        actions: List of {"at": ms, "pos": 0-100} dicts.

    Returns:
        Dict with duration_s, duration_fmt, action_count, avg_speed,
        max_speed, min_pos, max_pos, avg_pos. Empty dict if no actions.
    """
    if not actions:
        return {}

    import numpy as np

    times = [a["at"] for a in actions]
    positions = [a["pos"] for a in actions]

    times_s = np.array(times) / 1000.0
    pos_arr = np.array(positions)
    duration_s = times_s[-1] - times_s[0]

    dt = np.diff(times_s)
    dp = np.diff(pos_arr)
    speeds = np.abs(dp / np.where(dt > 0, dt, 1e-6))

    m, s = divmod(int(duration_s), 60)
    h, m = divmod(m, 60)
    duration_fmt = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    return {
        "duration_s": float(duration_s),
        "duration_fmt": duration_fmt,
        "action_count": len(times),
        "avg_speed": float(np.mean(speeds)),
        "max_speed": float(np.max(speeds)),
        "min_pos": int(np.min(pos_arr)),
        "max_pos": int(np.max(pos_arr)),
        "avg_pos": float(np.mean(pos_arr)),
    }


# ── Time axis helpers ────────────────────────────────────────────────────────


def _compute_ticks(
    start_ms: int, end_ms: int, max_ticks: int = 20,
) -> tuple[list[int], list[str]]:
    """Return (tickvals, ticktext) for a human-readable time axis."""
    span = end_ms - start_ms
    candidates = [500, 1_000, 5_000, 10_000, 30_000, 60_000, 120_000,
                  300_000, 600_000, 900_000, 1_800_000]
    step = candidates[-1]
    for c in candidates:
        if span / c <= max_ticks:
            step = c
            break

    first = ceil(start_ms / step) * step
    vals = list(range(first, end_ms + 1, step))
    texts = [_format_ms(v) for v in vals]
    return vals, texts


def _format_ms(ms: int) -> str:
    """Format milliseconds as M:SS or M:SS.t."""
    total_s = ms // 1000
    m = total_s // 60
    s = total_s % 60
    sub = ms % 1000
    if sub == 0:
        return f"{m}:{s:02d}"
    return f"{m}:{s:02d}.{sub // 100}"


# ── Colour math ──────────────────────────────────────────────────────────────


def _interpolate_color(stops: list[tuple[float, str]], t: float) -> str:
    """Interpolate a hex colour from a list of (position, hex) stops."""
    t = max(0.0, min(1.0, t))
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for i in range(1, len(stops)):
        p0, c0 = stops[i - 1]
        p1, c1 = stops[i]
        if p0 <= t <= p1:
            frac = (t - p0) / (p1 - p0)
            return _lerp_hex(c0, c1, frac)
    return stops[-1][1]


def _lerp_hex(c0: str, c1: str, t: float) -> str:
    """Linearly interpolate between two hex colours."""
    r0, g0, b0 = _hex_to_rgb(c0)
    r1, g1, b1 = _hex_to_rgb(c1)
    r = int(r0 + (r1 - r0) * t)
    g = int(g0 + (g1 - g0) * t)
    b = int(b0 + (b1 - b0) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
