"""Tests for file picker core logic."""

import tempfile
from pathlib import Path

from forge_ui_components.file_picker.core import (
    FUNSCRIPT_PICKER,
    VIDEO_PICKER,
    AUDIO_PICKER,
    CAPTIONS_PICKER,
    FilePickerConfig,
    clear_file,
    is_new_upload,
    mark_processed,
    resolve_file_path,
)


# ── FilePickerConfig defaults ────────────────────────────────────────────────


def test_config_defaults():
    cfg = FilePickerConfig(media_type="test", label="Test")
    assert cfg.upload_key_prefix == "test_upload"
    assert cfg.session_path_key == "test_path"
    assert cfg.processed_key == "_test_processed"


def test_prebuilt_configs():
    assert FUNSCRIPT_PICKER.media_type == "funscript"
    assert "funscript" in FUNSCRIPT_PICKER.accepted_extensions
    assert VIDEO_PICKER.media_type == "video"
    assert "mp4" in VIDEO_PICKER.accepted_extensions
    assert AUDIO_PICKER.media_type == "audio"
    assert "mp3" in AUDIO_PICKER.accepted_extensions
    assert CAPTIONS_PICKER.media_type == "captions"
    assert "srt" in CAPTIONS_PICKER.accepted_extensions


# ── is_new_upload / mark_processed ───────────────────────────────────────────


def test_is_new_upload_true():
    session = {}
    assert is_new_upload(FUNSCRIPT_PICKER, "test.funscript", session) is True


def test_is_new_upload_false_after_mark():
    session = {}
    mark_processed(FUNSCRIPT_PICKER, "test.funscript", session)
    assert is_new_upload(FUNSCRIPT_PICKER, "test.funscript", session) is False


def test_is_new_upload_different_file():
    session = {}
    mark_processed(FUNSCRIPT_PICKER, "old.funscript", session)
    assert is_new_upload(FUNSCRIPT_PICKER, "new.funscript", session) is True


# ── resolve_file_path ────────────────────────────────────────────────────────


def test_resolve_prefers_project_path():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        project_path = f.name
    session = {"video_path": "/nonexistent/path.mp4"}
    assert resolve_file_path(VIDEO_PICKER, session, project_path=project_path) == project_path
    Path(project_path).unlink()


def test_resolve_falls_back_to_session():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        session_path = f.name
    session = {"video_path": session_path}
    assert resolve_file_path(VIDEO_PICKER, session, project_path=None) == session_path
    Path(session_path).unlink()


def test_resolve_returns_empty_when_nothing():
    session = {}
    assert resolve_file_path(VIDEO_PICKER, session) == ""


# ── clear_file ───────────────────────────────────────────────────────────────


def test_clear_file():
    session = {"video_path": "/some/path.mp4", "_video_processed": "path.mp4"}
    clear_file(VIDEO_PICKER, session)
    assert "video_path" not in session
    assert "_video_processed" not in session


def test_clear_file_noop_on_empty():
    session = {}
    clear_file(VIDEO_PICKER, session)  # should not raise
    assert session == {}
