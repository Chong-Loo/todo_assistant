from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QFrame,
    QVBoxLayout as InnerLayout,
)

from app.todo_manager import (
    clear_all_completed_todos,
    complete_all_todos,
    load_normalized_todos,
)
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

        title_row = QHBoxLayout()
        title = QLabel(self.title_text)
        title.setObjectName("SectionTitle")
        title_row.addWidget(title)
        title_row.addStretch(1)

        if self.mode in ("email", "manual"):
            self.complete_all_btn = QPushButton("一键全部完成")
            self.complete_all_btn.setObjectName("PrimaryButton")
            self.complete_all_btn.clicked.connect(self._complete_all)
            title_row.addWidget(self.complete_all_btn)
        elif self.mode == "done":
            self.clear_all_btn = QPushButton("一键清除全部")
            self.clear_all_btn.setObjectName("DangerButton")
            self.clear_all_btn.clicked.connect(self._clear_all_completed)
            title_row.addWidget(self.clear_all_btn)

        root.addLayout(title_row)

        if self.mode == "done":
            search_panel = QFrame()
            search_panel.setObjectName("PanelCard")

            search_layout = QVBoxLayout(search_panel)
            search_layout.setContentsMargins(16, 14, 16, 14)
            search_layout.setSpacing(10)

            kw_row = QHBoxLayout()
            kw_label = QLabel("关键字：")
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
        self.content.setObjectName("PanelCard")
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
            card.setProperty("highlight", True)
            card.style().unpolish(card)
            card.style().polish(card)
            QTimer.singleShot(2400, lambda: _clear_focus(card))

        def _clear_focus(c):
            c.setProperty("highlight", False)
            c.style().unpolish(c)
            c.style().polish(c)

        QTimer.singleShot(80, do_focus)
        return True

    def _complete_all(self):
        label = {"email": "邮件待办", "manual": "人工待办"}.get(self.mode, "")
        confirm = QMessageBox.question(
            self,
            "确认操作",
            f"确定将所有{label}标记为完成吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            count = complete_all_todos(source_type=self.mode)
            QMessageBox.information(self, "操作完成", f"已完成 {count} 条待办。")
            self.reload()
        except Exception as exc:
            QMessageBox.critical(self, "操作失败", str(exc))

    def _clear_all_completed(self):
        confirm = QMessageBox.question(
            self,
            "确认操作",
            "确定永久清除所有已完成待办吗？\n附件也会一并删除，此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            count = clear_all_completed_todos()
            QMessageBox.information(self, "操作完成", f"已清除 {count} 条已完成待办。")
            self.reload()
        except Exception as exc:
            QMessageBox.critical(self, "操作失败", str(exc))

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
