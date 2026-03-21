"""Framework-agnostic transform editor logic."""

from dataclasses import dataclass, field


@dataclass
class TransformConfig:
    """Configuration for a single transform."""

    name: str
    sliders: list[dict] = field(default_factory=list)
    # Each slider: {"key": str, "label": str, "min": float, "max": float, "default": float, "step": float}
    values: dict = field(default_factory=dict)

    def get_value(self, key: str) -> float:
        slider = next((s for s in self.sliders if s["key"] == key), None)
        return self.values.get(key, slider["default"] if slider else 0.0)

    def set_value(self, key: str, value: float):
        self.values[key] = value

    def to_dict(self) -> dict:
        return {"name": self.name, "values": dict(self.values)}

    @classmethod
    def from_dict(cls, data: dict, sliders: list[dict]) -> "TransformConfig":
        return cls(name=data["name"], sliders=sliders, values=data.get("values", {}))


def apply_transform_preview(
    before_actions: list[dict],
    transform_fn: callable,
    config: TransformConfig,
) -> list[dict]:
    """Apply a transform function to funscript actions for preview.

    Args:
        before_actions: Original funscript actions.
        transform_fn: Callable(actions, config) -> transformed actions.
        config: Current slider values.

    Returns:
        Transformed actions list.
    """
    return transform_fn(before_actions, config)
