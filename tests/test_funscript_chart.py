"""Tests for funscript chart core logic."""

from forge_ui_components.funscript_chart.core import prepare_chart_data


def test_prepare_chart_data():
    actions = [{"at": 0, "pos": 0}, {"at": 1000, "pos": 50}, {"at": 2000, "pos": 100}]
    result = prepare_chart_data(actions)
    assert result["times"] == [0.0, 1.0, 2.0]
    assert result["positions"] == [0, 50, 100]


def test_prepare_chart_data_empty():
    result = prepare_chart_data([])
    assert result["times"] == []
    assert result["positions"] == []
