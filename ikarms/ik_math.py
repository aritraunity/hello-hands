"""Mathematical helpers for inverse kinematics."""

import math

from PySide6.QtCore import QPointF

from ikarms.models import ArmPose


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value between minimum and maximum."""
    return max(min(value, maximum), minimum)


def solve_two_bone_ik(
    shoulder: QPointF,
    target: QPointF,
    upper_length: float,
    lower_length: float,
    pivot_angle: int,
) -> ArmPose:
    """Solve a two-bone inverse kinematics pose."""
    delta_x = target.x() - shoulder.x()
    delta_y = target.y() - shoulder.y()
    distance = math.hypot(delta_x, delta_y)

    max_reach = upper_length + lower_length
    min_reach = abs(upper_length - lower_length)
    clamped_distance = clamp(distance, min_reach, max_reach)

    base_angle = math.atan2(delta_y, delta_x)
    pivot_radians = math.radians(pivot_angle)

    cosine_angle = (
        upper_length**2
        + clamped_distance**2
        - lower_length**2
    ) / (2.0 * upper_length * clamped_distance)
    cosine_angle = clamp(cosine_angle, -1.0, 1.0)

    shoulder_offset = math.acos(cosine_angle)
    upper_angle = base_angle - shoulder_offset + pivot_radians

    elbow = QPointF(
        shoulder.x() + math.cos(upper_angle) * upper_length,
        shoulder.y() + math.sin(upper_angle) * upper_length,
    )

    wrist = QPointF(
        shoulder.x() + math.cos(base_angle) * clamped_distance,
        shoulder.y() + math.sin(base_angle) * clamped_distance,
    )

    return ArmPose(shoulder=shoulder, elbow=elbow, wrist=wrist)


def calculate_extended_point(
    start_point: QPointF,
    reference_point: QPointF,
    length: float,
) -> QPointF:
    """Extend from start point away from reference point."""
    angle = math.atan2(
        start_point.y() - reference_point.y(),
        start_point.x() - reference_point.x(),
    )

    return QPointF(
        start_point.x() + math.cos(angle) * length,
        start_point.y() + math.sin(angle) * length,
    )