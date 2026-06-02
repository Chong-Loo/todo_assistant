from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QWidget,
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


def _deadline_within_days(todo: dict, days: int) -> bool:
    deadline = todo.get("deadline")
    if not deadline:
        return False
    try:
        dl = datetime.strptime(deadline[:10], "%Y-%m-%d")
        return dl <= datetime.now() + timedelta(days=days)
    except ValueError:
        return False


class DeadlinePopup(QDialog):
    todo_selected = Signal(str)

    def __init__(self, title_text: str, todos: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title_text)
        self.setModal(False)
        self.resize(520, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(f"{title_text}（{len(todos)} 条）")
        title.setStyleSheet("font-size: 18px; font-weight: 900; color: #111827;")
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        for todo in todos:
            card = self._make_todo_row(todo)
            layout.addWidget(card)

        layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _make_todo_row(self, todo: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("RecentTodoCard")
        frame.setCursor(Qt.PointingHandCursor)
        frame.todo_id = str(todo.get("id", ""))
        frame.setStyleSheet("""
            QFrame#RecentTodoCard {
                background: #ffffff;
                border: 1px solid #e5eaf1;
                border-radius: 14px;
            }
            QFrame#RecentTodoCard:hover {
                background: #fbfdff;
                border: 1px solid #bfdbfe;
            }
        """)

        row = QHBoxLayout(frame)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title = QLabel(str(todo.get("title") or "未命名"))
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #111827;")
        title.setWordWrap(True)
        text_col.addWidget(title)

        deadline = todo.get("deadline") or "无截止"
        meta = QLabel(f"截止：{deadline}")
        meta.setStyleSheet("font-size: 12px; color: #64748b;")
        text_col.addWidget(meta)

        row.addLayout(text_col, 1)

        priority = todo.get("priority", "normal")
        bg, fg, _border = PRIORITY_STYLES.get(priority, PRIORITY_STYLES["normal"])
        badge = QLabel(PRIORITY_LABELS.get(priority, ""))
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 8px; "
            f"padding: 4px 10px; font-size: 12px; font-weight: 800;"
        )
        row.addWidget(badge, 0, Qt.AlignVCenter)

        frame.mousePressEvent = lambda e, fid=frame.todo_id: (
            self.todo_selected.emit(fid) if e.button() == Qt.LeftButton else None,
            self.close()
        ) and None

        return frame


class MetricCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, value: int, clickable: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        if clickable:
            self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("MetricLabel")
        layout.addWidget(title_label)

        value_label = QLabel(str(value))
        value_label.setObjectName("MetricValue")
        layout.addWidget(value_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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
    待办概览：
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

        title = QLabel("主页")
        title.setObjectName("SectionTitle")
        self.root.addWidget(title)

        hint = QLabel("方框可点击查看筛选列表，待办清单可选择排序方式，点击卡片可跳转到详情。")
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

        recent_header = QHBoxLayout()
        recent_title = QLabel("未完成待办清单")
        recent_title.setObjectName("SectionTitle")
        recent_header.addWidget(recent_title)
        recent_header.addStretch(1)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("截止时间", "deadline")
        self.sort_combo.addItem("优先级", "priority")
        self.sort_combo.addItem("创建时间", "created_at")
        self.sort_combo.addItem("邮件/人工", "source")
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 800;
                color: #334155;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
        """)
        self.sort_combo.currentIndexChanged.connect(self.reload)
        recent_header.addWidget(self.sort_combo)

        panel_layout.addLayout(recent_header)

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

        self._overdue_todos = [
            todo for todo in active if is_todo_overdue(todo)
        ]
        self._urgent_todos = [
            todo for todo in active
            if todo.get("priority") == "urgent"
        ]
        self._high_todos = [
            todo for todo in active
            if todo.get("priority") == "high"
        ]
        self._deadline_soon = [
            todo for todo in active
            if _deadline_within_days(todo, 3)
        ]

        while self.metrics_row.count():
            item = self.metrics_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        cards = [
            ("全部待办", len(active), False, None),
            ("逾期", len(self._overdue_todos), True, self._show_overdue_popup),
            ("紧急", len(self._urgent_todos), True, self._show_urgent_popup),
            ("高优先级", len(self._high_todos), True, self._show_high_popup),
            ("三天内截止", len(self._deadline_soon), True, self._show_deadline_popup),
        ]
        for title, value, clickable, slot in cards:
            card = MetricCard(title, value, clickable=clickable)
            if slot:
                card.clicked.connect(slot)
            self.metrics_row.addWidget(card)

        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        sort_key = self.sort_combo.currentData()
        PRIORITY_ORDER = {"urgent": 0, "high": 1, "normal": 2, "low": 3}

        def sort_fn(t):
            if sort_key == "deadline":
                dl = t.get("deadline") or "9999-99-99"
                return dl[:10]
            elif sort_key == "priority":
                return PRIORITY_ORDER.get(t.get("priority", "normal"), 99)
            elif sort_key == "source":
                return 0 if t.get("is_manual") else 1
            else:
                return t.get("created_at") or ""

        sorted_active = sorted(active, key=sort_fn)

        if not sorted_active:
            empty = QLabel("暂无未完成待办。")
            empty.setObjectName("SectionHint")
            self.recent_layout.addWidget(empty)
            self.recent_layout.addStretch(1)
            return

        for todo in sorted_active:
            card = RecentTodoCard(todo)
            card.clicked.connect(self.todo_selected.emit)
            self.recent_layout.addWidget(card)

        self.recent_layout.addStretch(1)

    def _show_overdue_popup(self):
        if not self._overdue_todos:
            return
        popup = DeadlinePopup("逾期待办", self._overdue_todos, self)
        popup.todo_selected.connect(self.todo_selected.emit)
        popup.show()

    def _show_urgent_popup(self):
        if not self._urgent_todos:
            return
        popup = DeadlinePopup("紧急待办", self._urgent_todos, self)
        popup.todo_selected.connect(self.todo_selected.emit)
        popup.show()

    def _show_high_popup(self):
        if not self._high_todos:
            return
        popup = DeadlinePopup("高优先级待办", self._high_todos, self)
        popup.todo_selected.connect(self.todo_selected.emit)
        popup.show()

    def _show_deadline_popup(self):
        if not self._deadline_soon:
            return
        popup = DeadlinePopup("三天内截止待办", self._deadline_soon, self)
        popup.todo_selected.connect(self.todo_selected.emit)
        popup.show()
