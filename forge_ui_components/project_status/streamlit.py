"""Thin Streamlit render layer for project status sidebar.

Reads from a ProjectStatus snapshot — no session state access here.
The caller (app.py) builds the ProjectStatus from session state and
passes it in.
"""

from __future__ import annotations

import streamlit as st

from .core import ProjectStatus


def render_sidebar_status(status: ProjectStatus):
    """Render the read-only project status in Streamlit sidebar.

    Call this from within `st.sidebar` context.
    """
    if not status.has_project:
        st.caption("Drop a funscript on the **Project** tab to get started.")
        return

    # Workflow progress
    st.caption(status.workflow_line())

    # Tone and devices
    if status.tone_name:
        st.caption(f"🎨 Tone: **{status.tone_name}**")
    if status.device_targets:
        st.caption(f"📱 Devices: {', '.join(status.device_targets)}")

    # Undo + next step
    if status.has_undo:
        st.caption(f"Last: **{status.last_action_tab}** — {status.last_action_desc}")
    if status.next_step_name:
        st.caption(f"Next: **{status.next_step_name}** — {status.next_step_desc}")


def render_sidebar_specs(status: ProjectStatus):
    """Render project specs section in sidebar."""
    if not status.has_assessment:
        return

    st.markdown("**Project Specs**")
    st.caption("\n\n".join(status.spec_lines()))


def render_sidebar_transforms(status: ProjectStatus):
    """Render available transforms section in sidebar."""
    if not status.transform_categories:
        return

    st.markdown("**Available Transforms**")
    st.caption("\n\n".join(status.transform_lines()))


def render_sidebar_editing(status: ProjectStatus):
    """Render editing progress section in sidebar."""
    if not status.has_edits:
        return

    st.markdown("**Editing Progress**")
    st.caption("\n\n".join(status.editing_lines()))


def render_full_sidebar_status(status: ProjectStatus):
    """Render all status sections in sequence.

    Convenience function that calls all individual render functions.
    """
    render_sidebar_status(status)
    if status.has_assessment:
        render_sidebar_specs(status)
        render_sidebar_transforms(status)
        render_sidebar_editing(status)
