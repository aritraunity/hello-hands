"""Main window for the IK Arms application."""

from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from ikarms.animation import (
    AnimationPlayer,
    AnimationPreset,
    load_animation_presets,
)
from ikarms.canvas import ArmCanvas
from ikarms.controls import ControlPanel


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        self.setWindowTitle("IK Arms")
        self.setMinimumSize(900, 600)

        self.canvas = ArmCanvas()
        self.controls = ControlPanel()
        self.animation_player = AnimationPlayer()
        self.animation_presets = self._load_presets()

        self.controls.add_animation_buttons(self.animation_presets)
        self._connect_signals()

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.canvas, stretch=1)
        main_layout.addWidget(self.controls)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self.controls.target_changed.connect(self.canvas.set_target)
        self.controls.pivot_changed.connect(self.canvas.set_pivot_angle)
        self.controls.claw_changed.connect(self.canvas.set_claw_value)
        self.controls.animation_requested.connect(self._play_animation)
        self.animation_player.frame_changed.connect(self._apply_animation_frame)

    def _load_presets(self) -> tuple[AnimationPreset, ...]:
        """Load animation presets from disk."""
        project_root = Path(__file__).resolve().parent.parent
        preset_directory = project_root / "presets"
        return load_animation_presets(preset_directory)

    def _play_animation(self, label: str) -> None:
        """Play the requested animation."""
        preset_lookup = {
            preset.label: preset
            for preset in self.animation_presets
        }
        self.animation_player.play(preset_lookup[label])

    def _apply_animation_frame(
        self,
        target_x: int,
        target_y: int,
        pivot_angle: int,
        claw_value: int,
    ) -> None:
        """Apply animation frame values to the UI and canvas."""
        self.controls.apply_frame_values(
            target_x,
            target_y,
            pivot_angle,
            claw_value,
        )
        self.canvas.set_target(target_x, target_y)
        self.canvas.set_pivot_angle(pivot_angle)
        self.canvas.set_claw_value(claw_value)