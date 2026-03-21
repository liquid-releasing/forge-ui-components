"""Framework-agnostic beat bar logic."""

from dataclasses import dataclass


@dataclass
class BeatData:
    """Beat detection results."""

    beat_times: list[float]  # seconds
    bpm: float
    source_file: str

    def to_dict(self) -> dict:
        return {
            "beat_times": self.beat_times,
            "bpm": self.bpm,
            "source_file": self.source_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BeatData":
        return cls(
            beat_times=data["beat_times"],
            bpm=data["bpm"],
            source_file=data["source_file"],
        )


def generate_beats(audio_path: str) -> BeatData:
    """Run librosa beat detection on an audio file.

    Args:
        audio_path: Path to audio file.

    Returns:
        BeatData with detected beats and BPM.
    """
    import librosa

    y, sr = librosa.load(audio_path)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    return BeatData(
        beat_times=beat_times,
        bpm=float(tempo) if not hasattr(tempo, '__len__') else float(tempo[0]),
        source_file=audio_path,
    )
