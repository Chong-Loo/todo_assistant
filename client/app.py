import sys
import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db import init_db
from app.settings import get_theme_preference, resolve_default_theme
from client.main_window import MainWindow
from client.styles import set_app_stylesheet


def _get_system_theme() -> str:
    app = QApplication.instance()
    try:
        is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        return "dark" if is_dark else "light"
    except AttributeError:
        palette = app.palette()
        c = palette.color(QPalette.Window)
        luminance = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
        return "dark" if luminance < 128 else "light"


def _resolve_theme() -> str:
    """获取最终生效的主题：优先使用独立保存的主题偏好，否则使用默认配置"""
    preferred = get_theme_preference()
    if preferred:
        return preferred
    return resolve_default_theme()


def _load_and_apply_theme():
    theme = _resolve_theme()
    if theme == "system":
        is_dark = _get_system_theme() == "dark"
    else:
        is_dark = theme == "dark"
    set_app_stylesheet(is_dark)


def _on_palette_changed():
    theme = _resolve_theme()
    if theme == "system":
        is_dark = _get_system_theme() == "dark"
        set_app_stylesheet(is_dark)


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

    app.paletteChanged.connect(_on_palette_changed)

    icon_path = _resolve_icon_path()
    if icon_path and icon_path.exists():
        try:
            app.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    app_font = QFont("Microsoft YaHei", 10)
    app.setFont(app_font)

    _load_and_apply_theme()

    window = MainWindow()
    if icon_path and icon_path.exists():
        try:
            window.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
