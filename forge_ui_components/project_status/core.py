"""Framework-agnostic project status logic."""

from dataclasses import dataclass, field


@dataclass
class ProjectStatus:
    """Read-only project status for sidebar display."""

    project_name: str = ""
    funscript_name: str = ""
    action_count: int = 0
    duration_seconds: float = 0.0
    cycle_count: int = 0
    tabs_completed: dict[str, bool] = field(default_factory=dict)
    # assessment results (populated after Accept)
    phrase_count: int = 0
    pattern_count: int = 0
    bpm: float = 0.0

    @property
    def duration_display(self) -> str:
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        return f"{mins}:{secs:02d}"

    @property
    def has_assessment(self) -> bool:
        return self.phrase_count > 0

    def workflow_progress(self) -> list[tuple[str, bool]]:
        """Return ordered list of (tab_name, completed) for display."""
        tab_order = ["Project", "Device", "Tone", "Phrases", "Patterns", "Export"]
        return [(tab, self.tabs_completed.get(tab, False)) for tab in tab_order]
