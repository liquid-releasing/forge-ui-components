"""Tests for funscript chart core logic."""

from forge_ui_components.funscript_chart.core import (
    PointSeries,
    compute_chart_data,
    funscript_stats,
    monochrome_figure,
    prepare_chart_data,
    slice_series,
    vibrant_figure,
    _interpolate_color,
    _VELOCITY_STOPS,
)


# ── prepare_chart_data ───────────────────────────────────────────────────────


def test_prepare_chart_data():
    actions = [{"at": 0, "pos": 0}, {"at": 1000, "pos": 50}, {"at": 2000, "pos": 100}]
    result = prepare_chart_data(actions)
    assert result["times_s"] == [0.0, 1.0, 2.0]
    assert result["positions"] == [0, 50, 100]


def test_prepare_chart_data_empty():
    result = prepare_chart_data([])
    assert result["times_s"] == []
    assert result["positions"] == []


# ── compute_chart_data ───────────────────────────────────────────────────────


def test_compute_chart_data_basic():
    actions = [{"at": 0, "pos": 0}, {"at": 100, "pos": 50}, {"at": 200, "pos": 100}]
    series = compute_chart_data(actions)
    assert len(series.times_ms) == 3
    assert len(series.colors_velocity) == 3
    assert len(series.colors_amplitude) == 3
    assert series.positions == [0.0, 50.0, 100.0]


def test_compute_chart_data_empty():
    series = compute_chart_data([])
    assert series.times_ms == []
    assert series.positions == []


def test_compute_chart_data_velocity_normalized():
    actions = [{"at": 0, "pos": 0}, {"at": 100, "pos": 100}]
    series = compute_chart_data(actions)
    # Second point has max velocity → norm = 1.0
    assert series.velocity_norm[1] == 1.0


# ── slice_series ─────────────────────────────────────────────────────────────


def test_slice_series():
    series = PointSeries(
        times_ms=[0, 100, 200, 300, 400],
        positions=[0, 25, 50, 75, 100],
        velocities=[0, 0.25, 0.25, 0.25, 0.25],
        velocity_norm=[0, 1, 1, 1, 1],
        amplitude_norm=[0, 0.25, 0.5, 0.75, 1.0],
        colors_velocity=["#a"] * 5,
        colors_amplitude=["#b"] * 5,
    )
    sliced = slice_series(series, 100, 300)
    assert sliced.times_ms == [100, 200, 300]
    assert sliced.positions == [25, 50, 75]


def test_slice_series_empty():
    series = PointSeries(times_ms=[0, 100], positions=[0, 50],
                         velocities=[0, 0.5], velocity_norm=[0, 1],
                         amplitude_norm=[0, 0.5],
                         colors_velocity=["#a", "#b"],
                         colors_amplitude=["#c", "#d"])
    sliced = slice_series(series, 500, 600)
    assert sliced.times_ms == []


# ── monochrome_figure ────────────────────────────────────────────────────────


def test_monochrome_figure():
    fig = monochrome_figure([0, 1, 2], [0, 50, 100])
    assert fig.layout.height == 180
    assert len(fig.data) == 1
    assert fig.data[0].mode == "lines"


def test_monochrome_figure_compact():
    fig = monochrome_figure([0, 1], [0, 100], height=150, show_axes=False)
    assert fig.layout.height == 150
    assert fig.layout.xaxis.showticklabels is False


# ── vibrant_figure ───────────────────────────────────────────────────────────


def test_vibrant_figure_basic():
    actions = [{"at": i * 100, "pos": i * 10} for i in range(20)]
    series = compute_chart_data(actions)
    fig = vibrant_figure(series, [], height=300)
    assert fig.layout.height == 300
    assert len(fig.data) > 0


# ── funscript_stats ──────────────────────────────────────────────────────────


def test_funscript_stats():
    actions = [{"at": 0, "pos": 0}, {"at": 1000, "pos": 50}, {"at": 2000, "pos": 100}]
    stats = funscript_stats(actions)
    assert stats["action_count"] == 3
    assert stats["duration_fmt"] == "0:02"
    assert stats["min_pos"] == 0
    assert stats["max_pos"] == 100


def test_funscript_stats_empty():
    assert funscript_stats([]) == {}


# ── colour interpolation ────────────────────────────────────────────────────


def test_interpolate_color_boundaries():
    assert _interpolate_color(_VELOCITY_STOPS, 0.0) == "#1a2fff"
    assert _interpolate_color(_VELOCITY_STOPS, 1.0) == "#ff1a1a"


def test_interpolate_color_mid():
    color = _interpolate_color(_VELOCITY_STOPS, 0.5)
    assert color.startswith("#")
    assert len(color) == 7
