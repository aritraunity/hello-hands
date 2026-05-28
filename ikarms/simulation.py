"""Headless arm simulation helpers for server streaming."""

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF

from ikarms.animation import (
    AnimationFrame,
    AnimationPreset,
    interpolate_frame,
)
from ikarms.ik_math import calculate_extended_point, solve_two_bone_ik


CANVAS_WIDTH = 900.0
CANVAS_HEIGHT = 600.0
SHOULDER = QPointF(200.0, 320.0)
UPPER_LENGTH = 190.0
LOWER_LENGTH = 170.0
WRIST_LENGTH = 45.0
FINGER_LENGTH = 55.0


@dataclass(frozen=True)
class NormalizedPoint:
    """A normalized 2D point."""

    x: float
    y: float

    def to_dict(self) -> dict[str, float]:
        """Convert point to JSON-safe dictionary."""
        return {
            "x": round(self.x, 4),
            "y": round(self.y, 4),
        }


def build_animation_frames(
    preset: AnimationPreset,
) -> tuple[AnimationFrame, ...]:
    """Expand keyframes into interpolated frames."""
    if len(preset.frames) <= 1:
        return preset.frames

    expanded_frames: list[AnimationFrame] = []

    for frame_index in range(len(preset.frames) - 1):
        start_frame = preset.frames[frame_index]
        end_frame = preset.frames[frame_index + 1]
        duration_steps = max(end_frame.duration_steps, 1)

        for step_index in range(duration_steps + 1):
            progress = step_index / float(duration_steps)
            expanded_frames.append(
                interpolate_frame(start_frame, end_frame, progress)
            )

    return tuple(expanded_frames)


def frame_to_payload(frame: AnimationFrame) -> dict[str, object]:
    """Convert one animation frame into normalized streamed payload."""
    target = QPointF(float(frame.target_x), float(frame.target_y))
    pose = solve_two_bone_ik(
        shoulder=SHOULDER,
        target=target,
        upper_length=UPPER_LENGTH,
        lower_length=LOWER_LENGTH,
        pivot_angle=frame.pivot_angle,
    )

    wrist_tip = calculate_extended_point(
        start_point=pose.wrist,
        reference_point=pose.elbow,
        length=WRIST_LENGTH,
    )

    fingers = _calculate_fingers(
        elbow=pose.elbow,
        wrist=pose.wrist,
        wrist_tip=wrist_tip,
        claw_value=frame.claw_value,
    )

    return {
        "controls": {
            "target_x": frame.target_x,
            "target_y": frame.target_y,
            "pivot_angle": frame.pivot_angle,
            "claw_value": frame.claw_value,
        },
        "points": {
            "shoulder": _normalize_point(pose.shoulder).to_dict(),
            "elbow": _normalize_point(pose.elbow).to_dict(),
            "wrist": _normalize_point(pose.wrist).to_dict(),
            "wrist_tip": _normalize_point(wrist_tip).to_dict(),
            "target": _normalize_point(target).to_dict(),
            "fingers": [
                {
                    "start": _normalize_point(wrist_tip).to_dict(),
                    "end": _normalize_point(finger_end).to_dict(),
                }
                for finger_end in fingers
            ],
        },
    }


def _calculate_fingers(
    elbow: QPointF,
    wrist: QPointF,
    wrist_tip: QPointF,
    claw_value: int,
) -> tuple[QPointF, ...]:
    """Calculate four finger endpoints."""
    wrist_angle = math.atan2(
        wrist.y() - elbow.y(),
        wrist.x() - elbow.x(),
    )
    spread = math.radians(10 + claw_value * 0.5)

    finger_angles = (
        wrist_angle - spread,
        wrist_angle - spread * 0.35,
        wrist_angle + spread * 0.35,
        wrist_angle + spread,
    )

    return tuple(
        QPointF(
            wrist_tip.x() + math.cos(angle) * FINGER_LENGTH,
            wrist_tip.y() + math.sin(angle) * FINGER_LENGTH,
        )
        for angle in finger_angles
    )


def _normalize_point(point: QPointF) -> NormalizedPoint:
    """Normalize a canvas-space point to 0..1 coordinates."""
    return NormalizedPoint(
        x=point.x() / CANVAS_WIDTH,
        y=point.y() / CANVAS_HEIGHT,
    )