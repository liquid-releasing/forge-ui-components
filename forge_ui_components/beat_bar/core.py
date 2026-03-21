"""Framework-agnostic beat bar logic.

Wraps videoflow.audio.AudioBeatMap for beat analysis and provides
visualization-ready data structures. All librosa logic lives in
videoflow — this module only adds forge-specific helpers and the
Plotly figure builder.

Dependencies:
    pip install videoflow[audio]   # for analyze_beats
    pip install mediatools         # for extract_audio (video → wav)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import plotly.graph_objects as go


def analyze_beats(audio_path: str | Path, *, source: str = "full") -> "AudioBeatMap":
    """Run beat analysis on an audio or video file.

    Thin wrapper around videoflow.audio.analyze_beats(). Accepts both
    audio files and video files (librosa can load audio from video directly).

    Args:
        audio_path: Path to audio or video file.
        source: "full" (default) or "percussive" (HPSS — filters vocals).

    Returns:
        videoflow.audio.AudioBeatMap with beats, BPM, energy, phrases.

    Raises:
        ImportError: If videoflow is not installed.
    """
    try:
        from videoflow.audio import analyze_beats as _analyze
    except ImportError:
        raise ImportError(
            "videoflow is required for beat analysis. "
            'Install it with: pip install "videoflow[audio]"'
        )
    return _analyze(str(audio_path), source=source)


def load_cached_beats(cache_path: str | Path) -> "AudioBeatMap | None":
    """Load a cached AudioBeatMap from JSON, or return None if not found."""
    try:
        from videoflow.audio import AudioBeatMap
    except ImportError:
        return None
    path = Path(cache_path)
    if not path.exists():
        return None
    try:
        return AudioBeatMap.load(path)
    except Exception:
        return None


def save_beats(beat_map: "AudioBeatMap", cache_path: str | Path) -> Path:
    """Save an AudioBeatMap to JSON for caching."""
    return beat_map.save(cache_path)


def beat_bar_figure(
    beat_times_ms: list[int],
    energy: list[float] | None = None,
    *,
    duration_ms: int = 0,
    height: int = 80,
    color: str = "#4C8BF5",
) -> go.Figure:
    """Build a Plotly beat bar visualization.

    Shows beat markers as vertical bars, optionally scaled by energy.

    Args:
        beat_times_ms: Beat timestamps in milliseconds.
        energy: Optional normalized energy (0.0-1.0) per beat. If provided,
            bar height reflects energy. Otherwise all bars are equal height.
        duration_ms: Total duration for x-axis range.
        height: Chart height in pixels.
        color: Bar color.

    Returns:
        plotly.graph_objects.Figure
    """
    if not beat_times_ms:
        return go.Figure()

    times_s = [t / 1000.0 for t in beat_times_ms]
    heights = energy if energy and len(energy) == len(beat_times_ms) else [1.0] * len(beat_times_ms)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=times_s,
        y=heights,
        width=0.05,
        marker_color=color,
        showlegend=False,
    ))

    x_max = duration_ms / 1000.0 if duration_ms else (times_s[-1] + 1.0)
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=20),
        xaxis=dict(
            title="Time (s)",
            range=[0, x_max],
            showgrid=False,
        ),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.05)",
        bargap=0,
    )
    return fig


def beat_stats(beat_map) -> dict:
    """Extract display stats from an AudioBeatMap.

    Args:
        beat_map: videoflow.audio.AudioBeatMap instance.

    Returns:
        Dict with bpm, beat_count, phrase_count, duration_fmt.
    """
    duration_s = beat_map.duration_ms / 1000.0
    m, s = divmod(int(duration_s), 60)

    return {
        "bpm": beat_map.bpm,
        "beat_count": len(beat_map.beats),
        "downbeat_count": len(beat_map.downbeats),
        "phrase_count": len(beat_map.phrases),
        "duration_fmt": f"{m}:{s:02d}",
    }
