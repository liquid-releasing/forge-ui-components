"""Chart cache — PointSeries per chain stage, on-demand PNG rendering.

Eliminates redundant chart computation across Streamlit tabs.
Each Accept computes PointSeries once; tabs render PNG from cache.

Usage in Streamlit:
    from forge_ui_components.funscript_chart.cache import ChartCache

    cache = ChartCache.from_session_state()
    cache.set_stage("device", actions)
    png = cache.render_png("device", bands=bands)
    st.image(png, use_container_width=True)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .core import AnnotationBand, PointSeries, compute_chart_data
from .static import render_static_chart, render_cv_strip


@dataclass
class ChartCache:
    """Cached chart data per chain stage.

    Stores PointSeries (expensive to compute) and renders PNG on demand
    (cheap from cached series). Invalidation cascades downstream:
    setting "device" clears "tone" and "phrases".
    """

    _series: Dict[str, PointSeries] = field(default_factory=dict)
    _bands: Optional[List[AnnotationBand]] = None
    _png_cache: Dict[str, bytes] = field(default_factory=dict)
    _original_actions: Optional[list] = None

    # Chain order — setting a stage invalidates everything after it
    _STAGES = ["original", "device", "tone", "phrases"]

    # ── Store / retrieve PointSeries ────────────────────────────────

    def set_stage(self, stage: str, actions: list[dict]) -> PointSeries:
        """Compute and cache PointSeries for a chain stage.

        Invalidates downstream stages and their PNG caches.
        Returns the computed PointSeries.
        """
        series = compute_chart_data(actions)
        self._series[stage] = series

        # Store original actions for CV strip rendering
        if stage == "original":
            self._original_actions = actions

        # Invalidate downstream
        idx = self._STAGES.index(stage) if stage in self._STAGES else -1
        for downstream in self._STAGES[idx + 1:]:
            self._series.pop(downstream, None)

        # Clear all PNG caches (stale after any stage change)
        self._png_cache.clear()

        return series

    def set_series(self, stage: str, series: PointSeries) -> None:
        """Cache a pre-computed PointSeries (skip computation)."""
        self._series[stage] = series
        # Invalidate downstream
        idx = self._STAGES.index(stage) if stage in self._STAGES else -1
        for downstream in self._STAGES[idx + 1:]:
            self._series.pop(downstream, None)
        self._png_cache.clear()

    def get_series(self, stage: str) -> Optional[PointSeries]:
        """Get cached PointSeries for a stage, or None."""
        return self._series.get(stage)

    def get_latest_series(self) -> tuple[Optional[PointSeries], str]:
        """Walk the chain backwards and return the most recent cached series."""
        for stage in reversed(self._STAGES):
            s = self._series.get(stage)
            if s and s.times_ms:
                return s, stage
        return None, ""

    # ── Phrase bands ────────────────────────────────────────────────

    def set_bands(self, bands: List[AnnotationBand]) -> None:
        """Cache phrase annotation bands. Clears PNG cache."""
        self._bands = bands
        self._png_cache.clear()

    def get_bands(self) -> List[AnnotationBand]:
        """Get cached bands, or empty list."""
        return self._bands or []

    # ── PNG rendering (cheap from cached PointSeries) ───────────────

    def render_png(
        self,
        stage: str,
        *,
        with_bands: bool = False,
        height_px: int = 250,
        width_px: int = 1400,
        show_labels: bool = True,
        title: str = "",
        color_mode: str = "velocity",
        selected_band: Optional[AnnotationBand] = None,
    ) -> Optional[bytes]:
        """Render a PNG from cached PointSeries.

        Returns cached PNG if available, otherwise renders and caches.
        Returns None if no PointSeries is cached for this stage.
        """
        series = self._series.get(stage)
        if not series or not series.times_ms:
            return None

        # Build cache key
        _key = f"{stage}_{color_mode}_{with_bands}_{height_px}_{width_px}_{show_labels}"
        if _key in self._png_cache:
            return self._png_cache[_key]

        bands = self._bands if with_bands else None

        png = render_static_chart(
            series, bands,
            color_mode=color_mode,
            height_px=height_px,
            width_px=width_px,
            show_labels=show_labels,
            selected_band=selected_band,
            title=title,
        )

        self._png_cache[_key] = png
        return png

    def render_latest_png(
        self,
        *,
        with_bands: bool = False,
        **kwargs,
    ) -> Optional[bytes]:
        """Render PNG from the most recent cached PointSeries."""
        series, stage = self.get_latest_series()
        if not series:
            return None
        return self.render_png(stage, with_bands=with_bands, **kwargs)

    # ── CV strip ────────────────────────────────────────────────────

    def render_cv_strip_png(
        self,
        actions: list[dict],
        *,
        title: str = "",
        height_px: int = 40,
        width_px: int = 1400,
    ) -> bytes:
        """Render a CV groove heatmap strip."""
        return render_cv_strip(
            actions, title=title,
            height_px=height_px, width_px=width_px,
        )

    # ── Invalidation ────────────────────────────────────────────────

    def clear_all(self) -> None:
        """Clear everything — new funscript loaded."""
        self._series.clear()
        self._bands = None
        self._png_cache.clear()
        self._original_actions = None

    def clear_from(self, stage: str) -> None:
        """Clear this stage and everything downstream."""
        idx = self._STAGES.index(stage) if stage in self._STAGES else 0
        for s in self._STAGES[idx:]:
            self._series.pop(s, None)
        self._png_cache.clear()

    # ── Streamlit integration ───────────────────────────────────────

    @staticmethod
    def from_session_state() -> "ChartCache":
        """Get or create the ChartCache from Streamlit session_state."""
        import streamlit as st
        _KEY = "_chart_cache"
        if _KEY not in st.session_state:
            st.session_state[_KEY] = ChartCache()
        return st.session_state[_KEY]

    # ── Helpers ─────────────────────────────────────────────────────

    def has_stage(self, stage: str) -> bool:
        """Check if a PointSeries is cached for this stage."""
        s = self._series.get(stage)
        return s is not None and bool(s.times_ms)

    @property
    def stages_cached(self) -> list[str]:
        """List of stages that have cached PointSeries."""
        return [s for s in self._STAGES if self.has_stage(s)]
