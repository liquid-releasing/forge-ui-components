"""Static PNG chart renderer using Matplotlib.

Fast, non-interactive charts for overview/preview use cases.
Color shows velocity (blue=slow → red=fast). Phrase boundaries
are baked into the image as white vertical lines + labels.

Use cases:
- Project tab: full funscript overview
- Device tab: before/after preview
- Tone tab: before/after preview
- Phrases overview: full funscript with phrase boundaries
- Stim: channel previews
- Export: final preview

For interactive editing (hover timestamps, split/join), use the
Plotly-based charts in streamlit.py instead.
"""

from __future__ import annotations

import io
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from .core import PointSeries, AnnotationBand, compute_chart_data


# Dark theme matching Streamlit
_BG_COLOR = "#0e1117"
_PLOT_BG = "#1a1d23"
_TEXT_COLOR = "#cccccc"
_GRID_COLOR = "#2a2d33"

# Velocity colormap: blue → cyan → green → yellow → red
_VELOCITY_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "velocity",
    ["#1a2fff", "#00bfff", "#00e000", "#ffdd00", "#ff1a1a"],
)

# Monochrome blue
_MONO_BLUE = "#4C8BF5"


def render_static_chart(
    series: PointSeries,
    bands: Optional[List[AnnotationBand]] = None,
    *,
    color_mode: str = "velocity",
    height_px: int = 250,
    width_px: int = 1400,
    show_labels: bool = True,
    selected_band: Optional[AnnotationBand] = None,
    title: str = "",
) -> bytes:
    """Render a funscript chart as a PNG image.

    Args:
        series: Pre-computed PointSeries (from compute_chart_data).
        bands: Optional phrase/pattern annotation bands.
        color_mode: "velocity" (blue→red) or "monochrome" (solid blue).
        height_px: Image height in pixels.
        width_px: Image width in pixels.
        show_labels: Show phrase labels (P1, P2, ...) at the top.
        selected_band: Highlight this band with a yellow border.
        title: Optional title text above chart.

    Returns:
        PNG image bytes.
    """
    dpi = 100
    fig_w = width_px / dpi
    fig_h = height_px / dpi

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_PLOT_BG)

    if not series.times_ms:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    times_s = np.array(series.times_ms, dtype=float) / 1000.0
    positions = np.array(series.positions, dtype=float)
    n = len(times_s)

    # ── Draw phrase boundaries ──────────────────────────────────────
    if bands:
        _phrase_idx = 0
        for band in bands:
            if band.kind != "phrase":
                continue
            b_start = band.start_ms / 1000.0
            b_end = band.end_ms / 1000.0

            is_selected = (
                selected_band is not None
                and band.start_ms == selected_band.start_ms
                and band.end_ms == selected_band.end_ms
            )

            if is_selected:
                # Bright white selection box
                ax.axvspan(b_start, b_end, facecolor="#ffffff10",
                           edgecolor="#ffffff", linewidth=3, zorder=1)
            else:
                # Alternating zebra stripe — odd phrases get subtle dark tint
                if _phrase_idx % 2 == 1:
                    ax.axvspan(b_start, b_end, facecolor="#00000025",
                               edgecolor="none", zorder=1)

                # Thick white boundary line at phrase start
                ax.axvline(b_start, color="white", linewidth=3,
                           alpha=0.85, zorder=7)

            # Labels — prominent with solid background
            if show_labels and band.name:
                ax.text(
                    b_start + (b_end - b_start) * 0.02, 97,
                    band.name,
                    fontsize=9, fontweight="bold",
                    color="white", alpha=1.0,
                    verticalalignment="top",
                    bbox=dict(boxstyle="square,pad=0.15",
                              facecolor="black", alpha=0.8, edgecolor="none"),
                    zorder=8,
                )

            _phrase_idx += 1

    # ── Draw the funscript ──────────────────────────────────────────
    if color_mode == "velocity" and n > 1:
        # Color-coded line segments using LineCollection (fast)
        from matplotlib.collections import LineCollection

        vel_norm = np.array(series.velocity_norm, dtype=float)

        # Build segments: [[x0,y0], [x1,y1]] for each pair
        points = np.column_stack([times_s, positions])
        segments = np.stack([points[:-1], points[1:]], axis=1)

        # Color by velocity of the second point in each segment
        colors = _VELOCITY_CMAP(vel_norm[1:])

        lc = LineCollection(segments, colors=colors, linewidths=1.2, zorder=3)
        ax.add_collection(lc)

        # Fill under the line with semi-transparent velocity color
        # Use a gradient fill approximation: just fill with dark overlay
        ax.fill_between(times_s, 0, positions, color=_MONO_BLUE,
                         alpha=0.08, zorder=2)
    else:
        # Monochrome
        ax.plot(times_s, positions, color=_MONO_BLUE, linewidth=1.2, zorder=3)
        ax.fill_between(times_s, 0, positions, color=_MONO_BLUE,
                         alpha=0.15, zorder=2)

    # ── Dim context outside selected phrase ─────────────────────────
    if selected_band is not None:
        _sel_start = selected_band.start_ms / 1000.0
        _sel_end = selected_band.end_ms / 1000.0
        _DIM_COLOR = "#0e1117b0"  # Darker semi-transparent overlay
        if times_s[0] < _sel_start:
            ax.axvspan(times_s[0], _sel_start, facecolor=_DIM_COLOR,
                       edgecolor="none", zorder=6)
        if _sel_end < times_s[-1]:
            ax.axvspan(_sel_end, times_s[-1], facecolor=_DIM_COLOR,
                       edgecolor="none", zorder=6)

    # ── Axes and labels ─────────────────────────────────────────────
    ax.set_xlim(times_s[0], times_s[-1])
    ax.set_ylim(0, 100)
    ax.set_ylabel("pos", color=_TEXT_COLOR, fontsize=8)

    # Format x-axis as mm:ss
    dur_s = times_s[-1] - times_s[0]
    if dur_s > 3600:
        # Hour+ format
        def _fmt(x, _):
            m, s = divmod(int(x), 60)
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    else:
        def _fmt(x, _):
            m, s = divmod(int(x), 60)
            return f"{m}:{s:02d}"

    ax.xaxis.set_major_formatter(plt.FuncFormatter(_fmt))
    ax.tick_params(colors=_TEXT_COLOR, labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(_GRID_COLOR)
    ax.spines["left"].set_color(_GRID_COLOR)

    if title:
        ax.set_title(title, color=_TEXT_COLOR, fontsize=10, pad=5)

    # ── Export to PNG ───────────────────────────────────────────────
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def render_monochrome_static(
    times_s: list[float],
    positions: list[float],
    *,
    height_px: int = 180,
    width_px: int = 1400,
    title: str = "",
) -> bytes:
    """Quick monochrome static chart — no assessment data needed.

    Args:
        times_s: Timestamps in seconds.
        positions: Position values (0-100).

    Returns:
        PNG image bytes.
    """
    series = PointSeries(
        times_ms=[int(t * 1000) for t in times_s],
        positions=list(positions),
    )
    return render_static_chart(
        series, color_mode="monochrome",
        height_px=height_px, width_px=width_px, title=title,
    )


def render_vibrant_static(
    actions: list[dict],
    bands: Optional[List[AnnotationBand]] = None,
    *,
    height_px: int = 250,
    width_px: int = 1400,
    show_labels: bool = True,
    selected_band: Optional[AnnotationBand] = None,
    title: str = "",
) -> bytes:
    """Compute chart data and render as vibrant static PNG.

    Convenience wrapper: actions → compute_chart_data → render_static_chart.

    Args:
        actions: Funscript actions [{"at": ms, "pos": 0-100}, ...].
        bands: Phrase annotation bands.

    Returns:
        PNG image bytes.
    """
    series = compute_chart_data(actions)
    return render_static_chart(
        series, bands,
        color_mode="velocity",
        height_px=height_px, width_px=width_px,
        show_labels=show_labels,
        selected_band=selected_band,
        title=title,
    )


# ── CV (Groove) heatmap strip ───────────────────────────────────────────

# CV colormap: red (mechanical) → yellow → green (groovy)
_CV_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "cv_groove",
    ["#ff2222", "#ff8800", "#ffdd00", "#88dd00", "#22cc44"],
)


def render_cv_strip(
    actions: list[dict],
    *,
    window_seconds: int = 60,
    height_px: int = 40,
    width_px: int = 1400,
    title: str = "",
    show_labels: bool = True,
) -> bytes:
    """Render a compact CV (groove) heatmap strip as PNG.

    Shows timing variation per window: red = mechanical, green = groovy.
    Helps visualize what Humanize changed — monotone sections go from
    red to green after Groove is applied.

    Args:
        actions: Funscript actions list.
        window_seconds: Window size for CV computation (default 60s).
        height_px: Strip height in pixels.
        width_px: Strip width in pixels.
        title: Optional label above strip.
        show_labels: Show "Mechanical" / "Groovy" labels.

    Returns:
        PNG image bytes.
    """
    if len(actions) < 10:
        return b""

    times = np.array([a["at"] for a in actions], dtype=float)
    pos = np.array([a["pos"] for a in actions], dtype=float)
    dt_ms = np.diff(times)
    dp_abs = np.abs(np.diff(pos))
    velocity = np.where(dt_ms > 0, dp_abs / dt_ms * 1000, 0)

    dur_s = (times[-1] - times[0]) / 1000
    dur_min = dur_s / 60
    window_ms = window_seconds * 1000

    # Compute CV per window
    cv_values = []
    cv_centers = []
    for s_min in range(0, int(dur_min) + 1):
        s_ms = s_min * 60000
        e_ms = s_ms + window_ms
        mask = (times[:-1] >= s_ms) & (times[:-1] < e_ms)
        v = velocity[mask]
        if len(v) > 5 and np.mean(v) > 0:
            cv = float(np.std(v) / np.mean(v))
        else:
            cv = 0.0
        cv_values.append(cv)
        cv_centers.append((s_ms + e_ms / 2) / 1000.0)

    if not cv_values:
        return b""

    # Normalize CV to [0, 1] for colormap (0 = mechanical, 0.5+ = groovy)
    # Cap at 0.5 for color mapping (anything above 0.5 is fully green)
    cv_norm = np.clip(np.array(cv_values) / 0.5, 0, 1)

    dpi = 100
    fig_w = width_px / dpi
    fig_h = height_px / dpi

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_PLOT_BG)

    # Draw colored blocks
    n_blocks = len(cv_values)
    block_width = dur_s / n_blocks if n_blocks > 0 else 1

    for i, (cv_n, cv_raw) in enumerate(zip(cv_norm, cv_values)):
        x_start = i * block_width
        color = _CV_CMAP(cv_n)
        ax.barh(0, block_width, left=x_start, height=1,
                color=color, edgecolor="none")

    ax.set_xlim(0, dur_s)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")

    if title:
        ax.set_title(title, color=_TEXT_COLOR, fontsize=9, pad=2, loc="left")

    if show_labels:
        # Compute overall stats
        cv_median = float(np.median(cv_values))
        n_mechanical = sum(1 for c in cv_values if c < 0.15)
        pct_mechanical = n_mechanical / len(cv_values) * 100
        label = f"Groove: CV {cv_median:.2f} · {pct_mechanical:.0f}% mechanical"
        ax.text(dur_s * 0.5, -0.4, label,
                fontsize=7, color=_TEXT_COLOR, alpha=0.7,
                ha="center", va="top")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.02,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()
