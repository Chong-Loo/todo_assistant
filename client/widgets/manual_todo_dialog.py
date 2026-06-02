from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFormLayout,
)

from app.todo_manager import add_manual_todo, add_todo_attachment, edit_manual_todo
from client.widgets.deadline_dialog import DeadlineEditDialog
from client.widgets.painted_combo_box import PaintedComboBox


PRIORITY_OPTIONS = [
    ("紧急", "urgent"),
    ("高优先级", "high"),
    ("普通", "normal"),
    ("低优先级", "low"),
]


class ManualTodoDialog(QDialog):
    def __init__(self, todo: dict | None = None, parent=None):
        super().__init__(parent)
        self.todo = todo
        self.is_edit = todo is not None
        self.setWindowTitle("编辑待办" if self.is_edit else "人工添加待办")
        self.resize(640, 650)
        self.setModal(True)

        self.file_paths: list[str] = []
        self.deadline_value: str | None = (todo.get("deadline") or None) if todo else None

        self._build_ui()
        if self.is_edit:
            self._populate_from_todo()

    def _populate_from_todo(self):
        self.title_input.setText(str(self.todo.get("title", "")))
        priority = self.todo.get("priority", "normal")
        idx = self.priority_combo.findData(priority)
        if idx >= 0:
            self.priority_combo.setCurrentIndex(idx)
        self.deadline_button.setText(self._deadline_button_text())
        self.content_input.setPlainText(str(self.todo.get("content") or self.todo.get("reason") or ""))
        self.note_input.setPlainText(str(self.todo.get("note") or ""))

    def _build_ui(self):
        self.setStyleSheet(
            """
            QPushButton#DeadlineSelectButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 11px 14px;
                text-align: left;
                font-size: 14px;
                color: #334155;
                font-weight: 800;
            }

            QPushButton#DeadlineSelectButton:hover {
                background: #f8fafc;
                border: 1px solid #94a3b8;
            }

            QPushButton#FileChooseButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 11px;
                padding: 9px 14px;
                font-weight: 800;
            }

            QPushButton#FileChooseButton:hover {
                background: #f8fafc;
                border: 1px solid #94a3b8;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(16)

        title = QLabel("人工添加待办")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入待办标题")

        self.priority_combo = PaintedComboBox()
        for label, value in PRIORITY_OPTIONS:
            self.priority_combo.addItem(label, value)
        self.priority_combo.setCurrentIndex(2)

        self.deadline_button = QPushButton(self._deadline_button_text())
        self.deadline_button.setObjectName("DeadlineSelectButton")
        self.deadline_button.clicked.connect(self._choose_deadline)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("填写具体内容、背景或执行说明")
        self.content_input.setMinimumHeight(120)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("可选备注")
        self.note_input.setMinimumHeight(80)

        form.addRow("待办标题", self.title_input)
        form.addRow("优先级", self.priority_combo)
        form.addRow("截止时间", self.deadline_button)
        form.addRow("具体内容", self.content_input)
        form.addRow("备注", self.note_input)

        root.addLayout(form)

        file_bar = QHBoxLayout()
        file_label = QLabel("相关文件")
        file_label.setObjectName("TodoMeta")
        file_bar.addWidget(file_label)
        file_bar.addStretch(1)

        choose_files = QPushButton("选择文件")
        choose_files.setObjectName("FileChooseButton")
        choose_files.clicked.connect(self._choose_files)
        file_bar.addWidget(choose_files)

        root.addLayout(file_bar)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)
        root.addWidget(self.file_list)

        actions = QHBoxLayout()
        actions.addStretch(1)

        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("SecondaryButton")
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(cancel_button)

        submit_button = QPushButton("保存待办")
        submit_button.setObjectName("PrimaryButton")
        submit_button.clicked.connect(self._submit)
        actions.addWidget(submit_button)

        root.addLayout(actions)

    def _deadline_button_text(self):
        if self.deadline_value:
            return f"📅 {self.deadline_value}"
        return "📅 点击选择截止时间"

    def _choose_deadline(self):
        dialog = DeadlineEditDialog(self.deadline_value, self)

        if dialog.exec():
            self.deadline_value = dialog.deadline_value
            self.deadline_button.setText(self._deadline_button_text())

    def _choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择待办相关文件",
            str(Path.home()),
            "所有文件 (*.*)"
        )

        if not paths:
            return

        for path in paths:
            if path not in self.file_paths:
                self.file_paths.append(path)
                self.file_list.addItem(QListWidgetItem(Path(path).name))

    def _submit(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "提示", "待办标题不能为空。")
            return

        priority = self.priority_combo.currentData()
        content = self.content_input.toPlainText().strip()
        note = self.note_input.toPlainText().strip()

        try:
            if self.is_edit:
                edit_manual_todo(
                    self.todo["id"],
                    title=title,
                    priority=priority,
                    deadline=self.deadline_value,
                    content=content,
                    note=note,
                )
            else:
                todo = add_manual_todo(
                    title=title,
                    priority=priority,
                    deadline=self.deadline_value,
                    content=content,
                    note=note
                )

                for file_path in self.file_paths:
                    path = Path(file_path)
                    add_todo_attachment(
                        todo["id"],
                        path.name,
                        path.read_bytes()
                    )

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
