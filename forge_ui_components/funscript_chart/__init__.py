"""Funscript chart component — monochrome (fast) and vibrant (color-coded) modes."""

from .core import (
    ANNOTATION_COLORS,
    MONO_BLUE,
    AnnotationBand,
    PointSeries,
    compute_annotation_bands,
    compute_chart_data,
    funscript_stats,
    monochrome_figure,
    prepare_chart_data,
    slice_bands,
    slice_series,
    vibrant_figure,
)

__all__ = [
    "ANNOTATION_COLORS",
    "MONO_BLUE",
    "AnnotationBand",
    "PointSeries",
    "compute_annotation_bands",
    "compute_chart_data",
    "funscript_stats",
    "monochrome_figure",
    "prepare_chart_data",
    "slice_bands",
    "slice_series",
    "vibrant_figure",
]
