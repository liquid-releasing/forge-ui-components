"""Beat bar component — wraps videoflow AudioBeatMap with visualization."""

from .core import (
    analyze_beats,
    beat_bar_figure,
    beat_stats,
    load_cached_beats,
    save_beats,
)

__all__ = [
    "analyze_beats",
    "beat_bar_figure",
    "beat_stats",
    "load_cached_beats",
    "save_beats",
]
