from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
)

from app.todo_manager import load_normalized_todos
from app.todo_status import is_todo_overdue


PRIORITY_LABELS = {
    "urgent": "紧急",
    "high": "高优先级",
    "normal": "普通",
    "low": "低优先级",
}

PRIORITY_STYLES = {
    "urgent": ("#fee2e2", "#b91c1c", "#fecaca"),
    "high": ("#ffedd5", "#c2410c", "#fed7aa"),
    "normal": ("#dbeafe", "#1d4ed8", "#bfdbfe"),
    "low": ("#dcfce7", "#15803d", "#bbf7d0"),
}


class MetricCard(QFrame):
    def __init__(self, title: str, value: int, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("MetricLabel")
        layout.addWidget(title_label)

        value_label = QLabel(str(value))
        value_label.setObjectName("MetricValue")
        layout.addWidget(value_label)


class PriorityBadge(QLabel):
    def __init__(self, priority: str, parent=None):
        super().__init__(PRIORITY_LABELS.get(priority, "普通"), parent)

        bg, fg, border = PRIORITY_STYLES.get(
            priority,
            PRIORITY_STYLES["normal"]
        )

        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 11px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 900;
            }}
            """
        )


class RecentTodoCard(QFrame):
    clicked = Signal(str)

    def __init__(self, todo: dict, parent=None):
        super().__init__(parent)
        self.todo = todo
        self.todo_id = str(todo.get("id", ""))

        self.setObjectName("RecentTodoCard")
        self.setCursor(Qt.PointingHandCursor)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QFrame#RecentTodoCard {
                background: #ffffff;
                border: 1px solid #e5eaf1;
                border-radius: 17px;
            }

            QFrame#RecentTodoCard:hover {
                background: #fbfdff;
                border: 1px solid #bfdbfe;
            }

            QLabel#RecentTodoTitle {
                font-size: 16px;
                font-weight: 900;
                color: #111827;
            }

            QLabel#RecentTodoMeta {
                font-size: 12px;
                color: #64748b;
            }

            QLabel#RecentTodoDeadline {
                background: #f8fafc;
                color: #475569;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 7px 10px;
                font-size: 13px;
                font-weight: 800;
            }
            """
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(8)

        title = QLabel(str(self.todo.get("title") or "未命名待办"))
        title.setObjectName("RecentTodoTitle")
        title.setWordWrap(True)
        left.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        priority = self.todo.get("priority", "normal")
        meta_row.addWidget(PriorityBadge(priority), 0, Qt.AlignLeft)

        if is_todo_overdue(self.todo):
            overdue = QLabel("逾期")
            overdue.setStyleSheet(
                """
                QLabel {
                    background: #fee2e2;
                    color: #991b1b;
                    border: 1px solid #fca5a5;
                    border-radius: 11px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: 900;
                }
                """
            )
            meta_row.addWidget(overdue, 0, Qt.AlignLeft)

        status_text = "已暂缓" if self.todo.get("status") == "snoozed" else "未完成"
        status = QLabel(status_text)
        status.setObjectName("RecentTodoMeta")
        status.setStyleSheet(
            """
            QLabel {
                background: #f8fafc;
                color: #475569;
                border: 1px solid #e2e8f0;
                border-radius: 11px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 800;
            }
            """
        )
        meta_row.addWidget(status, 0, Qt.AlignLeft)
        meta_row.addStretch(1)

        left.addLayout(meta_row)
        root.addLayout(left, 1)

        deadline = str(self.todo.get("deadline") or "无截止")
        deadline_label = QLabel(deadline)
        deadline_label.setObjectName("RecentTodoDeadline")
        deadline_label.setAlignment(Qt.AlignCenter)
        root.addWidget(deadline_label, 0, Qt.AlignVCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.todo_id:
            self.clicked.emit(self.todo_id)

        super().mousePressEvent(event)


class DashboardPage(QWidget):
    """
    今日概览：
    1. 最近未完成待办展示成卡片清单；
    2. 按优先级标记颜色；
    3. 点击卡片后把 todo_id 发送给主窗口完成跳转。
    """

    todo_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.reload()

    def _build_ui(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(18)

        title = QLabel("今日概览")
        title.setObjectName("SectionTitle")
        self.root.addWidget(title)

        hint = QLabel("点击任一未完成待办，可直接跳转到对应详情卡片。")
        hint.setObjectName("SectionHint")
        self.root.addWidget(hint)

        self.metrics_row = QHBoxLayout()
        self.metrics_row.setSpacing(14)
        self.root.addLayout(self.metrics_row)

        panel = QFrame()
        panel.setObjectName("PanelCard")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 16, 18, 18)
        panel_layout.setSpacing(14)

        recent_title = QLabel("最近未完成待办")
        recent_title.setObjectName("SectionTitle")
        panel_layout.addWidget(recent_title)

        self.recent_scroll = QScrollArea()
        self.recent_scroll.setWidgetResizable(True)

        self.recent_content = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_content)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_layout.setSpacing(12)

        self.recent_scroll.setWidget(self.recent_content)
        panel_layout.addWidget(self.recent_scroll, 1)

        self.root.addWidget(panel, 1)

    def reload(self):
        todos = load_normalized_todos(cleanup=True)

        active = [
            todo for todo in todos
            if todo.get("status", "open") in {"open", "snoozed"}
        ]

        open_count = sum(
            1 for todo in todos
            if todo.get("status", "open") == "open"
        )
        urgent_count = sum(
            1 for todo in active
            if todo.get("priority") == "urgent"
        )
        high_count = sum(
            1 for todo in active
            if todo.get("priority") == "high"
        )
        overdue_count = sum(
            1 for todo in active
            if is_todo_overdue(todo)
        )

        while self.metrics_row.count():
            item = self.metrics_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for title, value in [
            ("有效待办", len(active)),
            ("未完成", open_count),
            ("紧急", urgent_count),
            ("逾期", overdue_count),
            ("高优先级", high_count),
        ]:
            self.metrics_row.addWidget(MetricCard(title, value))

        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not active:
            empty = QLabel("暂无未完成待办。")
            empty.setObjectName("SectionHint")
            self.recent_layout.addWidget(empty)
            self.recent_layout.addStretch(1)
            return

        for todo in active:
            card = RecentTodoCard(todo)
            card.clicked.connect(self.todo_selected.emit)
            self.recent_layout.addWidget(card)

        self.recent_layout.addStretch(1)
