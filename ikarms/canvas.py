"""Drawing canvas for the IK Arms application."""

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ikarms.ik_math import calculate_extended_point, solve_two_bone_ik
from ikarms.models import ArmPose


class ArmCanvas(QWidget):
    """Canvas used to draw the robot arm."""

    def __init__(self) -> None:
        """Initialize the drawing canvas."""
        super().__init__()
        self.setMinimumSize(700, 500)

        self.target_x = 540
        self.target_y = 320
        self.pivot_angle = 0
        self.claw_value = 40

        self.upper_length = 190.0
        self.lower_length = 170.0
        self.wrist_length = 45.0
        self.finger_length = 55.0

    def set_target(self, target_x: int, target_y: int) -> None:
        """Set wrist target position."""
        self.target_x = target_x
        self.target_y = target_y
        self.update()

    def set_pivot_angle(self, pivot_angle: int) -> None:
        """Set IK elbow pivot angle in degrees."""
        self.pivot_angle = pivot_angle
        self.update()

    def set_claw_value(self, claw_value: int) -> None:
        """Set claw openness value."""
        self.claw_value = claw_value
        self.update()

    def paintEvent(self, event) -> None:  # pylint: disable=invalid-name, unused-argument
        """Draw the robot arm."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pose = self._solve_pose()
        target = QPointF(float(self.target_x), float(self.target_y))

        self._draw_reach_guide(painter, pose.shoulder)
        self._draw_target_marker(painter, target)
        self._draw_base(painter, pose.shoulder)

        self._draw_segment(painter, pose.shoulder, pose.elbow, QColor(255, 0, 0), 10)
        self._draw_segment(painter, pose.elbow, pose.wrist, QColor(0, 255, 0), 10)

        wrist_tip = self._calculate_wrist_tip(pose)
        self._draw_segment(painter, pose.wrist, wrist_tip, QColor(0, 0, 255), 8)
        self._draw_claw(painter, pose, wrist_tip)

        self._draw_joint(painter, pose.shoulder, QColor(255, 255, 255))
        self._draw_joint(painter, pose.elbow, QColor(255, 255, 255))
        self._draw_joint(painter, pose.wrist, QColor(255, 255, 255))
        self._draw_legend(painter)

        painter.end()

    def _solve_pose(self) -> ArmPose:
        """Solve the current arm pose."""
        return solve_two_bone_ik(
            shoulder=QPointF(200.0, 320.0),
            target=QPointF(float(self.target_x), float(self.target_y)),
            upper_length=self.upper_length,
            lower_length=self.lower_length,
            pivot_angle=self.pivot_angle,
        )

    def _calculate_wrist_tip(self, pose: ArmPose) -> QPointF:
        """Calculate the wrist tip position."""
        return calculate_extended_point(
            start_point=pose.wrist,
            reference_point=pose.elbow,
            length=self.wrist_length,
        )

    def _draw_claw(
        self,
        painter: QPainter,
        pose: ArmPose,
        wrist_tip: QPointF,
    ) -> None:
        """Draw four claw fingers from the wrist tip."""
        wrist_angle = math.atan2(
            pose.wrist.y() - pose.elbow.y(),
            pose.wrist.x() - pose.elbow.x(),
        )
        spread = math.radians(10 + self.claw_value * 0.5)
        finger_angles = (
            wrist_angle - spread,
            wrist_angle - spread * 0.35,
            wrist_angle + spread * 0.35,
            wrist_angle + spread,
        )

        for finger_angle in finger_angles:
            finger_end = QPointF(
                wrist_tip.x() + math.cos(finger_angle) * self.finger_length,
                wrist_tip.y() + math.sin(finger_angle) * self.finger_length,
            )
            self._draw_segment(painter, wrist_tip, finger_end, QColor(255, 255, 0), 5)

    def _draw_reach_guide(self, painter: QPainter, shoulder: QPointF) -> None:
        """Draw the maximum IK reach boundary."""
        pen = QPen(QColor(80, 80, 80))
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        radius = self.upper_length + self.lower_length
        painter.drawEllipse(shoulder, radius, radius)

    @staticmethod
    def _draw_segment(
        painter: QPainter,
        start_point: QPointF,
        end_point: QPointF,
        color: QColor,
        width: int,
    ) -> None:
        """Draw one arm segment."""
        pen = QPen(color)
        pen.setWidth(width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(start_point, end_point)

    @staticmethod
    def _draw_joint(painter: QPainter, center: QPointF, color: QColor) -> None:
        """Draw a circular joint."""
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(color)
        radius = 8.0
        painter.drawEllipse(center, radius, radius)

    @staticmethod
    def _draw_target_marker(painter: QPainter, target: QPointF) -> None:
        """Draw the requested IK target position."""
        pen = QPen(QColor(255, 0, 255))
        pen.setWidth(2)
        painter.setPen(pen)

        size = 8.0
        painter.drawLine(
            QPointF(target.x() - size, target.y()),
            QPointF(target.x() + size, target.y()),
        )
        painter.drawLine(
            QPointF(target.x(), target.y() - size),
            QPointF(target.x(), target.y() + size),
        )

    @staticmethod
    def _draw_base(painter: QPainter, shoulder: QPointF) -> None:
        """Draw the robot arm base."""
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.setBrush(QColor(40, 40, 40))
        painter.drawRect(int(shoulder.x() - 35), int(shoulder.y() + 15), 70, 35)

    @staticmethod
    def _draw_legend(painter: QPainter) -> None:
        """Draw a simple RGB color legend."""
        painter.setPen(QPen(QColor(255, 255, 255), 1))

        legend_items = (
            ("Upper Arm", QColor(255, 0, 0)),
            ("Lower Arm", QColor(0, 255, 0)),
            ("Wrist", QColor(0, 0, 255)),
            ("Fingers", QColor(255, 255, 0)),
            ("Target", QColor(255, 0, 255)),
        )

        x_position = 20
        y_position = 25

        for index, item in enumerate(legend_items):
            label, color = item
            current_y = y_position + index * 22

            painter.setPen(QPen(color, 4))
            painter.drawLine(
                QPointF(float(x_position), float(current_y)),
                QPointF(float(x_position + 24), float(current_y)),
            )

            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(x_position + 32, current_y + 5, label)