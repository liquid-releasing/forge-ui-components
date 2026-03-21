"""Thin Streamlit render layer for file picker.

Renders the upload widget, processed guard, clear button, and file caption.
Stats rendering is handled by the caller since each file type has different
stats (funscript chart+metrics, video resolution+codec, audio format+bitrate).

Callbacks:
- on_upload: Called with (uploaded_file, config) when a new file is detected.
  Must return the resolved path string (after temp save, project copy, etc.).
- on_clear: Called with (config,) when the clear button is pressed.
  Should handle project cleanup, downstream state reset, etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st

from .core import FilePickerConfig, is_new_upload, mark_processed


def render_upload(
    config: FilePickerConfig,
    *,
    version: int = 0,
    on_upload: Callable | None = None,
    on_clear: Callable | None = None,
    current_path: str = "",
    show_clear: bool = True,
) -> str:
    """Render a file picker with upload guard, clear button, and file caption.

    Args:
        config: Picker configuration.
        version: Widget version counter (increment to force reset).
        on_upload: Callback(uploaded_file, config) -> resolved_path.
            If None, uploaded bytes are not saved (caller handles).
        on_clear: Callback(config) -> None. Called when clear button pressed.
        current_path: Currently resolved file path (for display and clear state).
        show_clear: Whether to show the clear button when a file is loaded.

    Returns:
        The current file path (may be updated by upload or cleared).
    """
    uploaded = st.file_uploader(
        config.label,
        type=config.accepted_extensions or None,
        key=f"{config.upload_key_prefix}_{version}",
        label_visibility="collapsed",
    )

    # New upload guard — only process once per filename
    if uploaded and is_new_upload(config, uploaded.name, st.session_state):
        if on_upload:
            resolved = on_upload(uploaded, config)
            if resolved:
                st.session_state[config.session_path_key] = resolved
                mark_processed(config, uploaded.name, st.session_state)
                st.rerun()

    # Display current file with clear button
    if current_path:
        if show_clear:
            col_name, col_clear = st.columns([6, 1])
            col_name.caption(f"{config.icon} {Path(current_path).name}")
            if col_clear.button("✕", key=f"clear_{config.media_type}", help=f"Remove {config.media_type}"):
                if on_clear:
                    on_clear(config)
                st.session_state.pop(config.session_path_key, None)
                st.session_state.pop(config.processed_key, None)
                st.rerun()
        else:
            st.caption(f"{config.icon} {Path(current_path).name}")

    return current_path
