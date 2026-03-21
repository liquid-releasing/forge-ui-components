"""Tests for beat bar core logic (no videoflow dependency needed)."""

from forge_ui_components.beat_bar.core import beat_bar_figure, beat_stats


# ── beat_bar_figure ──────────────────────────────────────────────────────────


def test_beat_bar_figure_basic():
    beats = [0, 500, 1000, 1500, 2000]
    fig = beat_bar_figure(beats, duration_ms=2500)
    assert fig.layout.height == 80
    assert len(fig.data) == 1
    assert len(fig.data[0].x) == 5


def test_beat_bar_figure_with_energy():
    beats = [0, 500, 1000]
    energy = [0.5, 1.0, 0.3]
    fig = beat_bar_figure(beats, energy=energy, duration_ms=1500)
    assert list(fig.data[0].y) == [0.5, 1.0, 0.3]


def test_beat_bar_figure_without_energy():
    beats = [0, 500, 1000]
    fig = beat_bar_figure(beats, duration_ms=1500)
    assert list(fig.data[0].y) == [1.0, 1.0, 1.0]


def test_beat_bar_figure_empty():
    fig = beat_bar_figure([])
    assert len(fig.data) == 0


def test_beat_bar_figure_custom_height():
    fig = beat_bar_figure([0, 1000], height=120, duration_ms=2000)
    assert fig.layout.height == 120


# ── beat_stats ───────────────────────────────────────────────────────────────


class _MockBeatMap:
    """Minimal mock of videoflow.audio.AudioBeatMap."""
    bpm = 120.0
    beats = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500]
    downbeats = [0, 2000]
    phrases = [(0, 3500)]
    energy = [0.5, 0.8, 1.0, 0.6, 0.9, 0.7, 0.4, 0.3]
    duration_ms = 4000


def test_beat_stats():
    stats = beat_stats(_MockBeatMap())
    assert stats["bpm"] == 120.0
    assert stats["beat_count"] == 8
    assert stats["downbeat_count"] == 2
    assert stats["phrase_count"] == 1
    assert stats["duration_fmt"] == "0:04"
