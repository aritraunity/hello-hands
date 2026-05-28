"""Entry point for the IK Arms PySide6 application."""

import sys

from PySide6.QtWidgets import QApplication

from ikarms.window import MainWindow


def main() -> int:
    """Run the PySide6 application."""
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())