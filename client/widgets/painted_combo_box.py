from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPalette
from PySide6.QtWidgets import QApplication, QComboBox


class PaintedComboBox(QComboBox):
    """
    单控件自绘下拉框。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setMinimumHeight(52)
        self.setMaximumHeight(52)
        self.setCursor(Qt.PointingHandCursor)
        self.setEditable(False)
        self.setFrame(False)
        self.setStyleSheet("""
            QComboBox {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)

    def _is_dark_mode(self):
        app = QApplication.instance()
        palette = app.palette()
        c = palette.color(QPalette.Window)
        return c.lightness() < 128

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        return QSize(max(base.width() + 38, 190), 52)

    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        return QSize(max(base.width() + 38, 170), 52)

    def paintEvent(self, event):
        is_dark = self._is_dark_mode()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(0.75, 0.75, self.width() - 1.5, self.height() - 1.5)
        radius = 13.0

        if is_dark:
            fill_color = QColor("#1e293b")
            border_color = QColor("#3b82f6") if self.hasFocus() else QColor("#475569")
            text_color = "#f1f5f9" if self.isEnabled() else "#64748b"
            arrow_color = QColor("#94a3b8")
        else:
            fill_color = QColor("#ffffff")
            border_color = QColor("#2563eb") if self.hasFocus() else QColor("#d7e0eb")
            text_color = "#1f2937" if self.isEnabled() else "#94a3b8"
            arrow_color = QColor("#64748b")

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, fill_color)
        painter.setPen(QPen(border_color, 1.3))
        painter.drawPath(path)

        text_rect = QRectF(16, 0, max(0, self.width() - 58), self.height())
        painter.setPen(QColor(text_color))
        painter.drawText(text_rect, int(Qt.AlignVCenter | Qt.AlignLeft), self.currentText())

        cx = self.width() - 25
        cy = self.height() / 2 + 1
        arrow = QPainterPath()
        arrow.moveTo(cx - 6, cy - 3)
        arrow.lineTo(cx, cy + 3)
        arrow.lineTo(cx + 6, cy - 3)
        painter.setPen(QPen(QColor(arrow_color), 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(arrow)

        painter.end()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()
