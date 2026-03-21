"""Framework-agnostic tone selector logic."""

from dataclasses import dataclass, field


@dataclass
class ToneCard:
    """Definition of a single tone option."""

    key: str
    title: str
    description: str
    sliders: list[dict] = field(default_factory=list)
    # Each slider: {"key": str, "label": str, "min": float, "max": float, "default": float, "step": float}


# Tone catalog — intensity order: Tender → Build → Tease → Edge → Climax → Dominant
TONE_CATALOG: list[ToneCard] = [
    ToneCard(
        key="tender",
        title="Tender",
        description="Gentle, smooth movements with gradual transitions.",
        sliders=[
            {"key": "smoothing", "label": "Smoothing", "min": 0.0, "max": 1.0, "default": 0.5, "step": 0.05},
            {"key": "range_limit", "label": "Range limit", "min": 0.0, "max": 1.0, "default": 0.7, "step": 0.05},
        ],
    ),
    ToneCard(
        key="build",
        title="Build",
        description="Gradually increasing intensity with momentum.",
        sliders=[
            {"key": "ramp_rate", "label": "Ramp rate", "min": 0.0, "max": 1.0, "default": 0.5, "step": 0.05},
            {"key": "ceiling", "label": "Ceiling", "min": 0.0, "max": 1.0, "default": 0.8, "step": 0.05},
            {"key": "momentum", "label": "Momentum", "min": 0.0, "max": 1.0, "default": 0.5, "step": 0.05},
        ],
    ),
    ToneCard(
        key="tease",
        title="Tease",
        description="Playful variations with intentional pauses and surges.",
        sliders=[
            {"key": "variation", "label": "Variation", "min": 0.0, "max": 1.0, "default": 0.6, "step": 0.05},
            {"key": "pause_freq", "label": "Pause frequency", "min": 0.0, "max": 1.0, "default": 0.3, "step": 0.05},
            {"key": "surge", "label": "Surge", "min": 0.0, "max": 1.0, "default": 0.5, "step": 0.05},
        ],
    ),
    ToneCard(
        key="edge",
        title="Edge",
        description="Sustained high intensity with controlled peaks.",
        sliders=[
            {"key": "sustain", "label": "Sustain", "min": 0.0, "max": 1.0, "default": 0.7, "step": 0.05},
            {"key": "peak_control", "label": "Peak control", "min": 0.0, "max": 1.0, "default": 0.6, "step": 0.05},
        ],
    ),
    ToneCard(
        key="climax",
        title="Climax",
        description="Maximum intensity with full dynamic range.",
        sliders=[
            {"key": "intensity", "label": "Intensity", "min": 0.0, "max": 1.0, "default": 0.9, "step": 0.05},
            {"key": "range", "label": "Range", "min": 0.0, "max": 1.0, "default": 1.0, "step": 0.05},
            {"key": "speed", "label": "Speed", "min": 0.0, "max": 1.0, "default": 0.8, "step": 0.05},
            {"key": "chaos", "label": "Chaos", "min": 0.0, "max": 1.0, "default": 0.3, "step": 0.05},
        ],
    ),
    ToneCard(
        key="dominant",
        title="Dominant",
        description="Commanding patterns with sharp transitions and authority.",
        sliders=[
            {"key": "sharpness", "label": "Sharpness", "min": 0.0, "max": 1.0, "default": 0.7, "step": 0.05},
            {"key": "authority", "label": "Authority", "min": 0.0, "max": 1.0, "default": 0.8, "step": 0.05},
            {"key": "rhythm_lock", "label": "Rhythm lock", "min": 0.0, "max": 1.0, "default": 0.5, "step": 0.05},
        ],
    ),
]


@dataclass
class ToneSelection:
    """Current tone selection state."""

    tone_key: str | None = None
    slider_values: dict = field(default_factory=dict)
    impact: float = 1.0

    def to_dict(self) -> dict:
        return {
            "tone_key": self.tone_key,
            "slider_values": dict(self.slider_values),
            "impact": self.impact,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ToneSelection":
        return cls(
            tone_key=data.get("tone_key"),
            slider_values=data.get("slider_values", {}),
            impact=data.get("impact", 1.0),
        )

    @property
    def selected_card(self) -> ToneCard | None:
        if self.tone_key is None:
            return None
        return next((c for c in TONE_CATALOG if c.key == self.tone_key), None)
