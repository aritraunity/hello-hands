"""Control panel widgets for the IK Arms application."""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ikarms.animation import AnimationPreset


class ControlPanel(QWidget):
    """Panel containing user controls."""

    target_changed = Signal(int, int)
    pivot_changed = Signal(int)
    claw_changed = Signal(int)
    animation_requested = Signal(str)

    def __init__(self) -> None:
        """Initialize the control panel."""
        super().__init__()

        self.target_x_label = QLabel()
        self.target_y_label = QLabel()
        self.pivot_label = QLabel()
        self.claw_label = QLabel()

        self.target_x_slider = self._create_slider(0, 900, 540)
        self.target_y_slider = self._create_slider(0, 600, 320)
        self.pivot_slider = self._create_slider(-180, 180, 0)
        self.claw_slider = self._create_slider(0, 100, 40)

        self.animation_layout = QVBoxLayout()

        layout = QVBoxLayout()
        layout.addWidget(self.target_x_label)
        layout.addWidget(self.target_x_slider)
        layout.addWidget(self.target_y_label)
        layout.addWidget(self.target_y_slider)
        layout.addWidget(self.pivot_label)
        layout.addWidget(self.pivot_slider)
        layout.addWidget(self.claw_label)
        layout.addWidget(self.claw_slider)
        layout.addSpacing(12)
        layout.addWidget(QLabel("Animations"))
        layout.addLayout(self.animation_layout)
        layout.addStretch()

        self.setLayout(layout)
        self.setFixedWidth(180)

        self.target_x_slider.valueChanged.connect(self._emit_target)
        self.target_y_slider.valueChanged.connect(self._emit_target)
        self.pivot_slider.valueChanged.connect(self._emit_pivot)
        self.claw_slider.valueChanged.connect(self._emit_claw)

        self._refresh_labels()

    def add_animation_buttons(
        self,
        presets: tuple[AnimationPreset, ...],
    ) -> None:
        """Create animation test buttons."""
        for preset in presets:
            button = QPushButton(preset.label)
            button.clicked.connect(self._create_animation_handler(preset.label))
            self.animation_layout.addWidget(button)

    def apply_frame_values(
        self,
        target_x: int,
        target_y: int,
        pivot_angle: int,
        claw_value: int,
    ) -> None:
        """Apply animation frame values to sliders."""
        self.target_x_slider.setValue(target_x)
        self.target_y_slider.setValue(target_y)
        self.pivot_slider.setValue(pivot_angle)
        self.claw_slider.setValue(claw_value)
        self._refresh_labels()

    def _create_animation_handler(self, label: str) -> Callable[[], None]:
        """Create a button callback for an animation label."""

        def handler() -> None:
            self.animation_requested.emit(label)

        return handler

    def _emit_target(self) -> None:
        """Emit current target slider values."""
        self._refresh_labels()
        self.target_changed.emit(
            self.target_x_slider.value(),
            self.target_y_slider.value(),
        )

    def _emit_pivot(self, pivot_angle: int) -> None:
        """Emit current pivot slider value."""
        self._refresh_labels()
        self.pivot_changed.emit(pivot_angle)

    def _emit_claw(self, claw_value: int) -> None:
        """Emit current claw slider value."""
        self._refresh_labels()
        self.claw_changed.emit(claw_value)

    def _refresh_labels(self) -> None:
        """Update control labels with current values."""
        self.target_x_label.setText(f"Target X: {self.target_x_slider.value()}")
        self.target_y_label.setText(f"Target Y: {self.target_y_slider.value()}")
        self.pivot_label.setText(f"Pivot Angle: {self.pivot_slider.value()}°")
        self.claw_label.setText(f"Claw Control: {self.claw_slider.value()}")

    @staticmethod
    def _create_slider(
        minimum: int,
        maximum: int,
        value: int,
    ) -> QSlider:
        """Create a horizontal slider."""
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        return slider