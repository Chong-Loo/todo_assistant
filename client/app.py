import sys
import os
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db import init_db
from client.main_window import MainWindow
from client.styles import APP_STYLESHEET


def _resolve_icon_path() -> Path:
    # env override
    env = os.environ.get("TODO_ASSISTANT_ICON")
    if env:
        p = Path(env)
        if p.exists():
            return p

    # project assets
    p = BASE_DIR / "assets" / "icon.ico"
    if p.exists():

        return p

    # frozen bundle extraction
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate = Path(meipass) / "assets" / "icon.ico"
            if candidate.exists():
                return candidate

        exe_parent = Path(sys.executable).resolve().parent
        candidate2 = exe_parent / "assets" / "icon.ico"
        if candidate2.exists():
            return candidate2

    return Path()


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("智能待办助手")

    # set application icon (so it's visible on taskbar)
    icon_path = _resolve_icon_path()
    if icon_path and icon_path.exists():
        try:
            app.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    app_font = QFont("Microsoft YaHei", 10)
    app.setFont(app_font)

    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    # also set window icon explicitly
    if icon_path and icon_path.exists():
        try:
            window.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
