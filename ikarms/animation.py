"""Animation loading and playback support."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal


DEFAULT_DURATION_STEPS = 14


@dataclass(frozen=True)
class AnimationFrame:
    """Single animation keyframe."""

    target_x: int
    target_y: int
    pivot_angle: int
    claw_value: int
    duration_steps: int = DEFAULT_DURATION_STEPS


@dataclass(frozen=True)
class AnimationPreset:
    """Named animation preset."""

    label: str
    frames: tuple[AnimationFrame, ...]


class AnimationLoadError(ValueError):
    """Raised when an animation preset cannot be loaded."""


class AnimationPlayer(QObject):
    """Timed animation player with linear interpolation."""

    frame_changed = Signal(int, int, int, int)
    animation_finished = Signal()

    def __init__(self, frame_duration_ms: int = 16) -> None:
        """Initialize the animation player."""
        super().__init__()
        self._frames: tuple[AnimationFrame, ...] = ()
        self._segment_index = 0
        self._step_index = 0

        self._timer = QTimer(self)
        self._timer.setInterval(frame_duration_ms)
        self._timer.timeout.connect(self._play_next_frame)

    def play(self, preset: AnimationPreset) -> None:
        """Play an animation preset."""
        self.stop()
        self._frames = preset.frames
        self._segment_index = 0
        self._step_index = 0

        if len(self._frames) == 1:
            self._emit_frame(self._frames[0])
            self.animation_finished.emit()
            return

        self._play_next_frame()
        self._timer.start()

    def stop(self) -> None:
        """Stop playback."""
        if self._timer.isActive():
            self._timer.stop()

    def _play_next_frame(self) -> None:
        """Emit the next interpolated animation frame."""
        if self._segment_index >= len(self._frames) - 1:
            self.stop()
            self.animation_finished.emit()
            return

        start_frame = self._frames[self._segment_index]
        end_frame = self._frames[self._segment_index + 1]
        duration_steps = max(end_frame.duration_steps, 1)

        progress = self._step_index / float(duration_steps)
        interpolated_frame = interpolate_frame(
            start_frame,
            end_frame,
            progress,
        )
        self._emit_frame(interpolated_frame)

        self._step_index += 1
        if self._step_index > duration_steps:
            self._step_index = 0
            self._segment_index += 1

    def _emit_frame(self, frame: AnimationFrame) -> None:
        """Emit an animation frame."""
        self.frame_changed.emit(
            frame.target_x,
            frame.target_y,
            frame.pivot_angle,
            frame.claw_value,
        )


def interpolate_frame(
    start_frame: AnimationFrame,
    end_frame: AnimationFrame,
    progress: float,
) -> AnimationFrame:
    """Linearly interpolate between two animation frames."""
    clamped_progress = max(min(progress, 1.0), 0.0)

    return AnimationFrame(
        target_x=lerp_int(
            start_frame.target_x,
            end_frame.target_x,
            clamped_progress,
        ),
        target_y=lerp_int(
            start_frame.target_y,
            end_frame.target_y,
            clamped_progress,
        ),
        pivot_angle=lerp_int(
            start_frame.pivot_angle,
            end_frame.pivot_angle,
            clamped_progress,
        ),
        claw_value=lerp_int(
            start_frame.claw_value,
            end_frame.claw_value,
            clamped_progress,
        ),
        duration_steps=end_frame.duration_steps,
    )


def lerp_int(start_value: int, end_value: int, progress: float) -> int:
    """Linearly interpolate between two integer values."""
    return round(start_value + (end_value - start_value) * progress)


def load_animation_preset(file_path: Path) -> AnimationPreset:
    """Load one animation preset from JSON."""
    try:
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))
        return _parse_animation_preset(raw_data)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise AnimationLoadError(
            f"Invalid animation preset: {file_path}"
        ) from error


def load_animation_presets(directory: Path) -> tuple[AnimationPreset, ...]:
    """Load all animation presets from a directory."""
    presets = [
        load_animation_preset(file_path)
        for file_path in sorted(directory.glob("*.json"))
    ]
    return tuple(presets)


def _parse_animation_preset(raw_data: dict[str, Any]) -> AnimationPreset:
    """Parse raw JSON data into an animation preset."""
    label = str(raw_data["label"])
    frames = tuple(
        AnimationFrame(
            target_x=int(frame["target_x"]),
            target_y=int(frame["target_y"]),
            pivot_angle=int(frame["pivot_angle"]),
            claw_value=int(frame["claw_value"]),
            duration_steps=int(
                frame.get("duration_steps", DEFAULT_DURATION_STEPS)
            ),
        )
        for frame in raw_data["frames"]
    )

    if not frames:
        raise AnimationLoadError("Animation preset must contain frames.")

    return AnimationPreset(label=label, frames=frames)