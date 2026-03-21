"""Tests for project status core logic."""

from forge_ui_components.project_status.core import ProjectStatus


def test_empty_status():
    status = ProjectStatus()
    assert not status.has_project
    assert not status.has_assessment
    assert not status.has_edits


def test_has_project():
    status = ProjectStatus(project_name="Test", funscript_name="test.funscript")
    assert status.has_project


def test_workflow_line_all_pending():
    status = ProjectStatus()
    line = status.workflow_line()
    assert "⬜ Project" in line
    assert "⬜ Export" in line
    assert "✅" not in line


def test_workflow_line_some_completed():
    status = ProjectStatus(tabs_completed={"Project": True, "Device": True})
    line = status.workflow_line()
    assert "✅ Project" in line
    assert "✅ Device" in line
    assert "⬜ Tone" in line


def test_spec_lines():
    status = ProjectStatus(
        phrase_count=5,
        transition_count=3,
        pattern_count=2,
        bpm_avg=120.0,
        bpm_min=80.0,
        bpm_max=160.0,
        assessment_elapsed_s=1.5,
    )
    lines = status.spec_lines()
    assert "● 5 phrases" in lines
    assert any("BPM avg: 120" in l for l in lines)
    assert any("80–160" in l for l in lines)
    assert any("1.5s" in l for l in lines)


def test_editing_lines():
    status = ProjectStatus(
        phrase_count=10,
        phrases_edited=3,
        pattern_instances_applied=5,
    )
    assert status.has_edits
    lines = status.editing_lines()
    assert any("3 / 10" in l for l in lines)
    assert any("5" in l for l in lines)


def test_transform_lines():
    status = ProjectStatus(
        transform_categories={"Amplitude": 3, "Structural": 2},
    )
    lines = status.transform_lines()
    assert "● Amplitude: 3" in lines
    assert "● Structural: 2" in lines
