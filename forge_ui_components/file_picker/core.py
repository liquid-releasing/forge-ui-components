"""Framework-agnostic file picker logic."""

from dataclasses import dataclass, field


@dataclass
class FilePickerState:
    """Tracks the state of a single file picker."""

    label: str
    accepted_extensions: list[str] = field(default_factory=list)
    file_data: bytes | None = None
    file_name: str | None = None
    stats: dict | None = None

    @property
    def has_file(self) -> bool:
        return self.file_data is not None

    def clear(self):
        self.file_data = None
        self.file_name = None
        self.stats = None


def compute_file_stats(file_name: str, file_data: bytes) -> dict:
    """Compute basic stats for an uploaded file.

    Returns:
        Dict with "name", "size_kb", and "extension".
    """
    return {
        "name": file_name,
        "size_kb": round(len(file_data) / 1024, 1),
        "extension": file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "",
    }
