"""Data models for the IK Arms application."""

from dataclasses import dataclass

from PySide6.QtCore import QPointF


@dataclass(frozen=True)
class ArmPose:
    """Computed joint positions for the robot arm."""

    shoulder: QPointF
    elbow: QPointF
    wrist: QPointF