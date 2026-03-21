"""Thin Streamlit render layer for project status sidebar."""

import streamlit as st

from .core import ProjectStatus


def render_sidebar_status(status: ProjectStatus):
    """Render the read-only project status in Streamlit sidebar."""
    if not status.project_name:
        st.caption("No project loaded")
        return

    st.markdown(f"**{status.project_name}**")
    if status.funscript_name:
        st.caption(status.funscript_name)

    # Quick stats
    st.markdown(
        f"{status.action_count} actions · {status.duration_display} · "
        f"{status.cycle_count} cycles"
    )

    # Assessment (only after Accept)
    if status.has_assessment:
        st.divider()
        st.markdown(
            f"{status.phrase_count} phrases · {status.pattern_count} patterns · "
            f"{status.bpm:.0f} BPM"
        )

    # Workflow progress
    st.divider()
    for tab_name, completed in status.workflow_progress():
        icon = "✅" if completed else "⬜"
        st.markdown(f"{icon} {tab_name}")
