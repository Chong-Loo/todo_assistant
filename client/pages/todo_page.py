from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QVBoxLayout as InnerLayout,
)

from app.todo_manager import load_normalized_todos
from client.widgets.todo_card import TodoCard


class TodoPage(QWidget):
    def __init__(
        self,
        title: str,
        mode: str,
        parent=None
    ):
        super().__init__(parent)
        self.title_text = title
        self.mode = mode
        self.card_map: dict[str, TodoCard] = {}
        self._build_ui()
        self.reload()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        title = QLabel(self.title_text)
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        if self.mode == "done":
            search_panel = QFrame()
            search_panel.setObjectName("PanelCard")
            search_panel.setStyleSheet(
                """
                QFrame#PanelCard {
                    background: white;
                    border: 1px solid #e5eaf1;
                    border-radius: 18px;
                }

                QLineEdit {
                    background: white;
                    border: 1px solid #cbd5e1;
                    border-radius: 10px;
                    padding: 8px 12px;
                    min-height: 36px;
                    max-height: 36px;
                }

                QLineEdit:focus {
                    border: 1px solid #2563eb;
                }

                QPushButton#ClearButton {
                    background: white;
                    border: 1px solid #cbd5e1;
                    color: #475569;
                    border-radius: 10px;
                    padding: 0px 18px;
                    min-height: 36px;
                    max-height: 36px;
                    font-weight: 700;
                }

                QPushButton#ClearButton:hover {
                    background: #f8fafc;
                    border: 1px solid #94a3b8;
                }
                """
            )

            search_layout = QVBoxLayout(search_panel)
            search_layout.setContentsMargins(16, 14, 16, 14)
            search_layout.setSpacing(10)

            kw_row = QHBoxLayout()
            kw_label = QLabel("关键字：")
            kw_label.setStyleSheet("font-weight: 700; color: #334155;")
            kw_label.setFixedWidth(70)
            self.search_keyword = QLineEdit()
            self.search_keyword.setPlaceholderText("搜索标题、内容、来源、依据...")
            kw_row.addWidget(kw_label)
            kw_row.addWidget(self.search_keyword, 1)

            clear_btn = QPushButton("清除")
            clear_btn.setObjectName("ClearButton")
            kw_row.addWidget(clear_btn)

            search_layout.addLayout(kw_row)
            root.addWidget(search_panel)

            self.search_keyword.textChanged.connect(self.reload)
            clear_btn.clicked.connect(self._clear_search)

        self.hint = QLabel("")
        self.hint.setObjectName("SectionHint")
        root.addWidget(self.hint)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.content = QFrame()
        self.content_layout = InnerLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)
        self.content_layout.addStretch(1)

        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

    def reload(self):
        todos = load_normalized_todos(cleanup=True)
        filtered = self._filter(todos)

        self.hint.setText(f"共 {len(filtered)} 条记录。")
        self.card_map = {}

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not filtered:
            empty = QLabel("暂无匹配待办。")
            empty.setObjectName("SectionHint")
            self.content_layout.addWidget(empty)
            self.content_layout.addStretch(1)
            return

        for todo in filtered:
            card = TodoCard(todo)
            card.changed.connect(self.reload)
            self.content_layout.addWidget(card)
            self.card_map[str(todo.get("id", ""))] = card

        self.content_layout.addStretch(1)

    def focus_todo(self, todo_id: str) -> bool:
        """
        延迟定位，避免页面刚切换时布局尚未完成，导致只跳页不滚动。
        """
        todo_id = str(todo_id)
        self.reload()

        card = self.card_map.get(todo_id)
        if card is None:
            return False

        def do_focus():
            self.scroll.ensureWidgetVisible(card, 0, 80)
            card.setStyleSheet(
                "QFrame#TodoCard { border: 2px solid #2563eb; background: #ffffff; }"
            )
            QTimer.singleShot(2400, lambda: card.setStyleSheet(""))

        QTimer.singleShot(80, do_focus)
        return True

    def _clear_search(self):
        self.search_keyword.clear()
        self.reload()

    def _filter(self, todos: list[dict]) -> list[dict]:
        if self.mode == "email":
            return [
                todo for todo in todos
                if not todo.get("is_manual")
                and todo.get("status", "open") in {"open", "snoozed"}
            ]

        if self.mode == "manual":
            return [
                todo for todo in todos
                if todo.get("is_manual")
                and todo.get("status", "open") in {"open", "snoozed"}
            ]

        if self.mode == "done":
            result = [
                todo for todo in todos
                if todo.get("status") == "done"
            ]

            keyword = self.search_keyword.text().strip().lower()
            if keyword:
                result = [
                    t for t in result
                    if keyword in str(t.get("title", "")).lower()
                    or keyword in str(t.get("content", "")).lower()
                    or keyword in str(t.get("reason", "")).lower()
                    or keyword in str(t.get("source_subject", "")).lower()
                ]

            result.sort(
                key=lambda t: t.get("completed_at") or t.get("updated_at") or "",
                reverse=True,
            )
            return result

        return todos
