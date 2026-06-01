from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QComboBox, QStyleOptionComboBox


class PaintedComboBox(QComboBox):
    """
    单控件自绘下拉框。

    设计目的：
    - 整个控件一次性绘制，避免“文本区 + 右侧箭头区”割裂；
    - 不依赖 SVG，也不依赖 Windows 原生复杂控件风格；
    - 保留 QComboBox 原生弹出列表、currentData、findData 等能力。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
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
                color: #1f2937;
            }

            QComboBox QAbstractItemView {
                background: #ffffff;
                color: #1f2937;
                border: 1px solid #cbd5e1;
                selection-background-color: #dbeafe;
                selection-color: #1d4ed8;
                outline: 0;
                padding: 4px;
            }
        """)

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        return QSize(max(base.width() + 38, 190), 52)

    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        return QSize(max(base.width() + 38, 170), 52)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(0.75, 0.75, self.width() - 1.5, self.height() - 1.5)
        radius = 13.0

        if self.hasFocus():
            border_color = QColor("#2563eb")
        else:
            border_color = QColor("#d7e0eb")

        fill_color = QColor("#ffffff")

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, fill_color)
        painter.setPen(QPen(border_color, 1.3))
        painter.drawPath(path)

        # 当前文本
        text_rect = QRectF(
            16,
            0,
            max(0, self.width() - 58),
            self.height()
        )
        painter.setPen(QColor("#1f2937") if self.isEnabled() else QColor("#94a3b8"))
        painter.drawText(
            text_rect,
            int(Qt.AlignVCenter | Qt.AlignLeft),
            self.currentText()
        )

        # 单体化箭头，不绘制右侧分割线，视觉更接近 Web 版
        cx = self.width() - 25
        cy = self.height() / 2 + 1

        arrow = QPainterPath()
        arrow.moveTo(cx - 6, cy - 3)
        arrow.lineTo(cx, cy + 3)
        arrow.lineTo(cx + 6, cy - 3)

        painter.setPen(QPen(QColor("#64748b"), 2.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(arrow)

        painter.end()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()
