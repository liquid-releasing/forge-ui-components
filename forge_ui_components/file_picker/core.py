"""Framework-agnostic file picker logic.

Provides the state management and upload-guard pattern used across all
FunScriptForge file pickers. Each picker tracks:
- Whether a file has been uploaded (via _processed guard)
- The resolved file path (from upload, session, or project storage)
- Stats computed from the file

The Streamlit render layer handles the actual st.file_uploader widget,
clear button, and stats display. Context-specific behavior (downstream
reset, project storage, disk space checks) is handled via callbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FilePickerConfig:
    """Configuration for a single file picker instance.

    Attributes:
        media_type: Identifier (e.g., "funscript", "video", "audio", "captions").
        label: Upload prompt text.
        accepted_extensions: List of file extensions without dots.
        icon: Emoji icon for the file display.
        upload_key_prefix: Base name for Streamlit widget keys.
        session_path_key: Session state key for the resolved file path.
        processed_key: Session state key for the upload guard.
    """

    media_type: str
    label: str
    accepted_extensions: list[str] = field(default_factory=list)
    icon: str = "📄"
    upload_key_prefix: str = ""
    session_path_key: str = ""
    processed_key: str = ""

    def __post_init__(self):
        if not self.upload_key_prefix:
            self.upload_key_prefix = f"{self.media_type}_upload"
        if not self.session_path_key:
            self.session_path_key = f"{self.media_type}_path"
        if not self.processed_key:
            self.processed_key = f"_{self.media_type}_processed"


# Pre-configured pickers for FunScriptForge
FUNSCRIPT_PICKER = FilePickerConfig(
    media_type="funscript",
    label="Drag and drop your funscript here",
    accepted_extensions=["funscript"],
    icon="📄",
)

VIDEO_PICKER = FilePickerConfig(
    media_type="video",
    label="Drag and drop your video here",
    accepted_extensions=["mp4", "mov", "avi", "mkv"],
    icon="📹",
)

AUDIO_PICKER = FilePickerConfig(
    media_type="audio",
    label="Drag and drop audio here",
    accepted_extensions=["mp3", "wav", "flac", "ogg"],
    icon="♪",
)

CAPTIONS_PICKER = FilePickerConfig(
    media_type="captions",
    label="Drag and drop captions here",
    accepted_extensions=["srt", "vtt", "ass"],
    icon="💬",
)


def resolve_file_path(
    config: FilePickerConfig,
    session_state: dict,
    project_path: str | None = None,
) -> str:
    """Resolve the current file path from project or session state.

    Priority: project-stored path > session state path.

    Args:
        config: Picker configuration.
        session_state: Streamlit session state dict.
        project_path: Path from project storage (e.g., get_input_file result).

    Returns:
        Resolved file path, or empty string if no file.
    """
    if project_path and Path(project_path).exists():
        return project_path
    sp = session_state.get(config.session_path_key, "")
    if sp and Path(sp).exists():
        return sp
    return ""


def is_new_upload(config: FilePickerConfig, uploaded_name: str, session_state: dict) -> bool:
    """Check if an uploaded file is new (not yet processed).

    Args:
        config: Picker configuration.
        uploaded_name: Name of the uploaded file.
        session_state: Streamlit session state dict.

    Returns:
        True if this is a new upload that hasn't been processed.
    """
    return session_state.get(config.processed_key) != uploaded_name


def mark_processed(config: FilePickerConfig, uploaded_name: str, session_state: dict):
    """Mark a file as processed to prevent re-processing on rerun."""
    session_state[config.processed_key] = uploaded_name


def clear_file(config: FilePickerConfig, session_state: dict):
    """Clear file state from session."""
    session_state.pop(config.session_path_key, None)
    session_state.pop(config.processed_key, None)
