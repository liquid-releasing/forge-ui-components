"""Framework-agnostic project status logic.

Collects read-only status data from session state and project objects
into a single ProjectStatus dataclass for display. The Streamlit render
layer reads this — no session state access in the render code.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectStatus:
    """Read-only project status snapshot for sidebar display."""

    # Project identity
    project_name: str = ""
    funscript_name: str = ""
    output_folder: str = ""

    # Workflow progress
    tabs_completed: dict[str, bool] = field(default_factory=dict)

    # Tone & device selections
    tone_name: str = ""
    device_targets: list[str] = field(default_factory=list)

    # Assessment stats (populated after Accept)
    phrase_count: int = 0
    transition_count: int = 0
    pattern_count: int = 0
    bpm_avg: float = 0.0
    bpm_min: float = 0.0
    bpm_max: float = 0.0
    assessment_elapsed_s: float | None = None

    # Editing progress
    phrases_edited: int = 0
    pattern_instances_applied: int = 0

    # Undo
    last_action_tab: str = ""
    last_action_desc: str = ""
    has_undo: bool = False

    # Next step
    next_step_name: str = ""
    next_step_desc: str = ""

    # Transform counts
    transform_categories: dict[str, int] = field(default_factory=dict)

    @property
    def has_project(self) -> bool:
        return bool(self.project_name and self.funscript_name)

    @property
    def has_assessment(self) -> bool:
        return self.phrase_count > 0

    @property
    def has_edits(self) -> bool:
        return self.phrases_edited > 0 or self.pattern_instances_applied > 0

    def workflow_line(self) -> str:
        """Build the ✅/⬜ workflow progress string."""
        tab_order = ["Project", "Device", "Tone", "Phrases", "Patterns", "Export"]
        parts = []
        for tab in tab_order:
            done = self.tabs_completed.get(tab, False)
            icon = "✅" if done else "⬜"
            parts.append(f"{icon} {tab}")
        return "  ".join(parts)

    def spec_lines(self) -> list[str]:
        """Build the project specs bullet list."""
        lines = [
            f"● {self.phrase_count} phrases",
            f"● {self.transition_count} transitions",
            f"● {self.pattern_count} patterns",
        ]
        if self.bpm_avg > 0:
            lines.append(f"● BPM avg: {self.bpm_avg:.0f}")
        if self.bpm_min > 0 and self.bpm_max > 0:
            lines.append(f"● Phrase BPM range: {self.bpm_min:.0f}–{self.bpm_max:.0f}")
        if self.assessment_elapsed_s is not None:
            lines.append(f"● Assessed in {self.assessment_elapsed_s:.1f}s")
        return lines

    def editing_lines(self) -> list[str]:
        """Build the editing progress bullet list."""
        lines = []
        if self.phrase_count:
            lines.append(f"● Phrases edited: {self.phrases_edited} / {self.phrase_count}")
        if self.pattern_instances_applied:
            lines.append(f"● Pattern instances applied: {self.pattern_instances_applied}")
        return lines

    def transform_lines(self) -> list[str]:
        """Build the available transforms bullet list."""
        return [f"● {cat}: {count}" for cat, count in self.transform_categories.items()]
