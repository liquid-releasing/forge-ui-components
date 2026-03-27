"""Tests for ChartCache — PointSeries caching per chain stage + PNG rendering."""

import pytest
from forge_ui_components.funscript_chart.cache import ChartCache
from forge_ui_components.funscript_chart.core import (
    AnnotationBand,
    PointSeries,
    compute_chart_data,
)


# ── Test fixtures ───────────────────────────────────────────────────────

def _make_actions(n=100, start_ms=0, step_ms=500):
    """Generate n simple zigzag actions."""
    return [
        {"at": start_ms + i * step_ms, "pos": (i % 2) * 100}
        for i in range(n)
    ]


def _make_bands(n_phrases=3, duration_ms=50000):
    """Generate n phrase annotation bands."""
    step = duration_ms // n_phrases
    return [
        AnnotationBand(
            kind="phrase", start_ms=i * step, end_ms=(i + 1) * step,
            label=f"P{i+1}", color="white", name=f"P{i+1}",
        )
        for i in range(n_phrases)
    ]


# ── ChartCache basics ──────────────────────────────────────────────────


class TestChartCacheBasics:
    def test_empty_cache(self):
        cache = ChartCache()
        assert cache.stages_cached == []
        assert cache.get_series("original") is None
        assert cache.get_latest_series() == (None, "")

    def test_set_stage(self):
        cache = ChartCache()
        actions = _make_actions(50)
        series = cache.set_stage("original", actions)
        assert isinstance(series, PointSeries)
        assert len(series.times_ms) == 50
        assert cache.has_stage("original")
        assert cache.stages_cached == ["original"]

    def test_set_multiple_stages(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(100))
        cache.set_stage("device", _make_actions(100))
        cache.set_stage("tone", _make_actions(100))
        assert cache.stages_cached == ["original", "device", "tone"]

    def test_get_latest_series(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_stage("device", _make_actions(60))
        series, stage = cache.get_latest_series()
        assert stage == "device"
        assert len(series.times_ms) == 60

    def test_set_series_directly(self):
        cache = ChartCache()
        series = compute_chart_data(_make_actions(30))
        cache.set_series("tone", series)
        assert cache.has_stage("tone")
        assert cache.get_series("tone") is series


# ── Invalidation ────────────────────────────────────────────────────────


class TestInvalidation:
    def test_set_stage_invalidates_downstream(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_stage("device", _make_actions(50))
        cache.set_stage("tone", _make_actions(50))
        cache.set_stage("phrases", _make_actions(50))
        assert cache.stages_cached == ["original", "device", "tone", "phrases"]

        # Setting device should clear tone and phrases
        cache.set_stage("device", _make_actions(50))
        assert cache.stages_cached == ["original", "device"]
        assert not cache.has_stage("tone")
        assert not cache.has_stage("phrases")

    def test_clear_from(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_stage("device", _make_actions(50))
        cache.set_stage("tone", _make_actions(50))

        cache.clear_from("tone")
        assert cache.stages_cached == ["original", "device"]

    def test_clear_from_device_clears_all_downstream(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_stage("device", _make_actions(50))
        cache.set_stage("tone", _make_actions(50))

        cache.clear_from("device")
        assert cache.stages_cached == ["original"]

    def test_clear_all(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_stage("device", _make_actions(50))
        cache.set_bands(_make_bands())
        cache.clear_all()
        assert cache.stages_cached == []
        assert cache.get_bands() == []

    def test_png_cache_cleared_on_stage_set(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        # Render a PNG to populate the cache
        png1 = cache.render_png("original", height_px=100, width_px=400)
        assert png1 is not None
        assert len(cache._png_cache) > 0

        # Setting device should clear PNG cache
        cache.set_stage("device", _make_actions(50))
        assert len(cache._png_cache) == 0


# ── Bands ───────────────────────────────────────────────────────────────


class TestBands:
    def test_set_and_get_bands(self):
        cache = ChartCache()
        bands = _make_bands(5)
        cache.set_bands(bands)
        assert len(cache.get_bands()) == 5

    def test_empty_bands(self):
        cache = ChartCache()
        assert cache.get_bands() == []

    def test_set_bands_clears_png_cache(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.render_png("original", height_px=100, width_px=400)
        assert len(cache._png_cache) > 0

        cache.set_bands(_make_bands())
        assert len(cache._png_cache) == 0


# ── PNG rendering ───────────────────────────────────────────────────────


class TestPNGRendering:
    def test_render_png_returns_bytes(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        png = cache.render_png("original", height_px=100, width_px=400)
        assert isinstance(png, bytes)
        assert len(png) > 100  # Not empty
        # PNG magic bytes
        assert png[:4] == b"\x89PNG"

    def test_render_png_cached(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        png1 = cache.render_png("original", height_px=100, width_px=400)
        png2 = cache.render_png("original", height_px=100, width_px=400)
        # Same object from cache
        assert png1 is png2

    def test_render_png_different_params_different_cache(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        png_small = cache.render_png("original", height_px=100, width_px=400)
        png_large = cache.render_png("original", height_px=300, width_px=800)
        assert png_small is not png_large
        assert len(png_large) > len(png_small)

    def test_render_png_missing_stage(self):
        cache = ChartCache()
        assert cache.render_png("tone") is None

    def test_render_with_bands(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_bands(_make_bands(3, duration_ms=25000))

        png_no_bands = cache.render_png("original", with_bands=False, height_px=100, width_px=400)
        png_with_bands = cache.render_png("original", with_bands=True, height_px=100, width_px=400)

        assert png_no_bands is not None
        assert png_with_bands is not None
        # With bands should be different (larger due to labels/lines)
        assert png_no_bands != png_with_bands

    def test_render_latest_png(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        cache.set_stage("device", _make_actions(60))

        png = cache.render_latest_png(height_px=100, width_px=400)
        assert png is not None
        assert png[:4] == b"\x89PNG"

    def test_render_monochrome(self):
        cache = ChartCache()
        cache.set_stage("original", _make_actions(50))
        png = cache.render_png("original", color_mode="monochrome", height_px=100, width_px=400)
        assert isinstance(png, bytes)
        assert len(png) > 100


# ── CV strip ────────────────────────────────────────────────────────────


class TestCVStrip:
    def test_render_cv_strip(self):
        cache = ChartCache()
        actions = _make_actions(500, step_ms=200)  # ~100s of data
        png = cache.render_cv_strip_png(actions, height_px=40, width_px=400)
        assert isinstance(png, bytes)
        assert len(png) > 100
        assert png[:4] == b"\x89PNG"

    def test_render_cv_strip_too_few_actions(self):
        cache = ChartCache()
        png = cache.render_cv_strip_png([{"at": 0, "pos": 0}])
        assert png == b""


# ── Static renderer ─────────────────────────────────────────────────────


class TestStaticRenderer:
    def test_render_vibrant_static(self):
        from forge_ui_components.funscript_chart.static import render_vibrant_static
        actions = _make_actions(200)
        png = render_vibrant_static(actions, height_px=100, width_px=400)
        assert isinstance(png, bytes)
        assert png[:4] == b"\x89PNG"

    def test_render_monochrome_static(self):
        from forge_ui_components.funscript_chart.static import render_monochrome_static
        times_s = [i * 0.5 for i in range(100)]
        positions = [(i % 2) * 100 for i in range(100)]
        png = render_monochrome_static(times_s, positions, height_px=100, width_px=400)
        assert isinstance(png, bytes)
        assert png[:4] == b"\x89PNG"

    def test_render_vibrant_with_bands(self):
        from forge_ui_components.funscript_chart.static import render_vibrant_static
        actions = _make_actions(200)
        bands = _make_bands(5, duration_ms=100000)
        png = render_vibrant_static(actions, bands, height_px=100, width_px=400)
        assert isinstance(png, bytes)
        assert len(png) > 100

    def test_render_vibrant_empty(self):
        from forge_ui_components.funscript_chart.static import render_vibrant_static
        png = render_vibrant_static([], height_px=100, width_px=400)
        assert isinstance(png, bytes)  # Returns empty chart PNG
