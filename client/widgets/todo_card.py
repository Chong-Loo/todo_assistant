from __future__ import annotations

from pathlib import Path
import os
import sys
import subprocess

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.todo_manager import (
    add_stage,
    add_todo_attachment,
    delete_stage,
    delete_todo_attachment,
    delete_todo,
    update_deadline,
    update_priority,
    update_status,
    update_stage_status,
)
from app.todo_status import is_todo_overdue
from client.widgets.deadline_dialog import DeadlineEditDialog
from client.widgets.mail_detail_dialog import MailDetailDialog


PRIORITY_OPTIONS = [
    ("紧急", "urgent"),
    ("高优先级", "high"),
    ("普通", "normal"),
    ("低优先级", "low"),
]

PRIORITY_OBJECTS = {
    "urgent": "BadgeUrgent",
    "high": "BadgeHigh",
    "normal": "BadgeNormal",
    "low": "BadgeLow",
}

PRIORITY_LABELS = {
    "urgent": "紧急",
    "high": "高优先级",
    "normal": "普通",
    "low": "低优先级",
}

STATUS_OBJECTS = {
    "open": "BadgeOpen",
    "snoozed": "BadgeSnoozed",
    "done": "BadgeDone",
    "cancelled": "BadgeCancelled",
}

STATUS_LABELS = {
    "open": "未完成",
    "snoozed": "已暂缓",
    "done": "已完成",
    "cancelled": "已取消",
}


class AttachmentRow(QFrame):
    delete_requested = Signal(str)

    def __init__(self, attachment: dict, parent=None):
        super().__init__(parent)
        self.attachment = attachment
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("AttachmentRow")
        self.setStyleSheet(
            """
            QFrame#AttachmentRow {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }

            QLabel#AttachmentName {
                font-size: 13px;
                font-weight: 800;
                color: #111827;
            }

            QLabel#AttachmentMeta {
                font-size: 12px;
                color: #64748b;
            }

            QPushButton#DeleteAttachmentButton {
                background: #ffffff;
                border: 1px solid #fecaca;
                color: #b91c1c;
                border-radius: 10px;
                padding: 7px 12px;
                font-weight: 800;
            }

            QPushButton#DeleteAttachmentButton:hover {
                background: #fef2f2;
                border: 1px solid #fca5a5;
            }
            """
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(12)

        file_name = self.attachment.get("name") or "未命名文件"
        file_size = int(self.attachment.get("size") or 0)
        upload_time = self.attachment.get("uploaded_at") or ""

        left = QVBoxLayout()
        left.setSpacing(4)

        name_label = QLabel(f"📎 {file_name}")
        name_label.setObjectName("AttachmentName")
        name_label.setWordWrap(True)
        left.addWidget(name_label)

        if file_size:
            size_text = f"{file_size / 1024:.1f} KB"
        else:
            size_text = "大小未知"

        meta_text = size_text if not upload_time else f"{size_text} · {upload_time}"
        meta_label = QLabel(meta_text)
        meta_label.setObjectName("AttachmentMeta")
        meta_label.setWordWrap(True)
        left.addWidget(meta_label)

        root.addLayout(left, 1)

        open_btn = QPushButton("打开")
        open_btn.setObjectName("OpenAttachmentButton")
        open_btn.clicked.connect(self._open_file)
        root.addWidget(open_btn, 0, Qt.AlignVCenter)

        open_folder_btn = QPushButton("所在目录")
        open_folder_btn.setObjectName("OpenAttachmentFolderButton")
        open_folder_btn.clicked.connect(self._open_folder)
        root.addWidget(open_folder_btn, 0, Qt.AlignVCenter)

        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("DeleteAttachmentButton")
        delete_btn.clicked.connect(self._emit_delete)
        root.addWidget(delete_btn, 0, Qt.AlignVCenter)

    def _emit_delete(self):
        path = str(self.attachment.get("path") or "")
        if path:
            self.delete_requested.emit(path)

    def _resolve_attachment_path(self) -> Path:
        # Resolve stored attachment path to absolute file system path.
        rel = str(self.attachment.get("path") or "").strip()
        if not rel:
            return Path()

        # If absolute path stored, return directly
        p = Path(rel)
        if p.is_absolute():
            return p

        try:
            from app.db import DATA_DIR
            base = Path(DATA_DIR)
        except Exception:
            base = Path.cwd()

        return (base / rel).resolve()

    def _open_file(self):
        p = self._resolve_attachment_path()
        if not p or not p.exists():
            QMessageBox.information(self, "提示", "附件文件不存在")
            return

        try:
            if os.name == 'nt':
                os.startfile(str(p))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(p)])
            else:
                subprocess.run(['xdg-open', str(p)])
        except Exception as e:
            QMessageBox.critical(self, "打开失败", str(e))

    def _open_folder(self):
        p = self._resolve_attachment_path()
        if not p or not p.exists():
            QMessageBox.information(self, "提示", "附件文件不存在")
            return

        folder = p.parent
        try:
            if os.name == 'nt':
                os.startfile(str(folder))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(folder)])
            else:
                subprocess.run(['xdg-open', str(folder)])
        except Exception as e:
            QMessageBox.critical(self, "打开失败", str(e))


class StageRow(QFrame):
    status_changed = Signal(int, str)
    delete_requested = Signal(int)

    def __init__(self, stage: dict, parent=None):
        super().__init__(parent)
        self.stage = stage
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("StageRow")
        self.setStyleSheet("""
            QFrame#StageRow {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
            QLabel#StageTitle {
                font-size: 13px;
                font-weight: 800;
                color: #111827;
            }
            QLabel#StageDeadline {
                font-size: 12px;
                color: #64748b;
            }
            QPushButton#StageCheck {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 16px;
                font-weight: 900;
                color: transparent;
                padding: 0px;
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
            }
            QPushButton#StageCheck:checked {
                background-color: #22c55e;
                border: 2px solid #22c55e;
                color: #ffffff;
            }
            QPushButton#StageCheck:hover {
                border-color: #94a3b8;
            }
            QPushButton#StageCheck:checked:hover {
                background-color: #16a34a;
                border-color: #16a34a;
            }
            QPushButton#DeleteStageButton {
                background: #ffffff;
                border: 1px solid #fecaca;
                color: #b91c1c;
                border-radius: 10px;
                padding: 7px 12px;
                font-weight: 800;
            }
            QPushButton#DeleteStageButton:hover {
                background: #fef2f2;
                border: 1px solid #fca5a5;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        self.checkbox = QPushButton()
        self.checkbox.setObjectName("StageCheck")
        self.checkbox.setCheckable(True)
        self.checkbox.setChecked(self.stage.get("status") == "done")
        self.checkbox.setText("✓" if self.stage.get("status") == "done" else "")
        self.checkbox.clicked.connect(self._on_toggle)
        root.addWidget(self.checkbox, 0, Qt.AlignVCenter)

        left = QVBoxLayout()
        left.setSpacing(2)

        title_label = QLabel(str(self.stage.get("title", "")))
        title_label.setObjectName("StageTitle")
        title_label.setWordWrap(True)

        if self.stage.get("status") == "done":
            title_label.setStyleSheet("QLabel#StageTitle { color: #9ca3af; text-decoration: line-through; }")

        left.addWidget(title_label)

        deadline = self.stage.get("deadline")
        if deadline:
            deadline_label = QLabel(f"截止：{deadline}")
            deadline_label.setObjectName("StageDeadline")
            left.addWidget(deadline_label)

        root.addLayout(left, 1)

        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("DeleteStageButton")
        delete_btn.clicked.connect(self._emit_delete)
        root.addWidget(delete_btn, 0, Qt.AlignVCenter)

    def _on_toggle(self, checked: bool):
        self.checkbox.setText("✓" if checked else "")
        new_status = "done" if checked else "pending"
        self.status_changed.emit(self.stage["id"], new_status)

    def _emit_delete(self):
        confirm = QMessageBox.question(
            self,
            "确认删除阶段",
            f"确定删除阶段「{self.stage.get('title', '')}」吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.delete_requested.emit(self.stage["id"])


class TodoCard(QFrame):
    changed = Signal()

    def __init__(self, todo: dict, parent=None):
        super().__init__(parent)
        self.todo = todo
        self.is_overdue = is_todo_overdue(todo)
        self.setObjectName("TodoCard")
        self._stage_deadline_value: str | None = None
        self._build_ui()

    def _badge(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(str(self.todo.get("title") or "未命名待办"))
        title.setObjectName("TodoTitle")
        title.setWordWrap(True)
        root.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)

        id_label = QLabel(f"ID：{self.todo.get('id', '')}")
        id_label.setObjectName("TodoMeta")
        meta_row.addWidget(id_label, 0, Qt.AlignVCenter)

        self.deadline_button = QPushButton(self._deadline_button_text())
        self.deadline_button.setObjectName("DeadlineInlineButton")
        self.deadline_button.clicked.connect(self._edit_deadline)
        self.deadline_button.setStyleSheet(
            """
            QPushButton#DeadlineInlineButton {
                background: #f8fafc;
                border: 1px solid #dbe3ee;
                color: #475569;
                border-radius: 12px;
                padding: 7px 12px;
                font-size: 13px;
                font-weight: 800;
                text-align: left;
            }

            QPushButton#DeadlineInlineButton:hover {
                background: #eef4fb;
                border: 1px solid #bfdbfe;
                color: #1d4ed8;
            }
            """
        )
        meta_row.addWidget(self.deadline_button, 0, Qt.AlignVCenter)
        meta_row.addStretch(1)
        root.addLayout(meta_row)

        badges = QHBoxLayout()

        current_priority = self.todo.get("priority", "normal")
        self.priority_btn = QPushButton(PRIORITY_LABELS.get(current_priority, current_priority))
        self.priority_btn.setObjectName(PRIORITY_OBJECTS.get(current_priority, "BadgeNormal"))
        self.priority_btn.setCursor(Qt.PointingHandCursor)
        self.priority_btn.setStyleSheet(
            "QPushButton#BadgeUrgent { background: #fee2e2; color: #b91c1c; border-radius: 10px; padding: 5px 10px; font-weight: 800; border: none; }"
            "QPushButton#BadgeHigh { background: #ffedd5; color: #c2410c; border-radius: 10px; padding: 5px 10px; font-weight: 800; border: none; }"
            "QPushButton#BadgeNormal { background: #dbeafe; color: #1d4ed8; border-radius: 10px; padding: 5px 10px; font-weight: 800; border: none; }"
            "QPushButton#BadgeLow { background: #dcfce7; color: #15803d; border-radius: 10px; padding: 5px 10px; font-weight: 800; border: none; }"
            "QPushButton#BadgeUrgent:hover { background: #fecaca; }"
            "QPushButton#BadgeHigh:hover { background: #fed7aa; }"
            "QPushButton#BadgeNormal:hover { background: #bfdbfe; }"
            "QPushButton#BadgeLow:hover { background: #bbf7d0; }"
        )
        self._priority_menu = QMenu(self)
        for label, value in PRIORITY_OPTIONS:
            action = self._priority_menu.addAction(label)
            action.setData(value)
            action.triggered.connect(lambda checked=False, v=value: self._change_priority(v))
        self.priority_btn.clicked.connect(self._show_priority_menu)
        badges.addWidget(self.priority_btn)

        if self.todo.get("is_manual"):
            badges.addWidget(self._badge("人工", "BadgeNormal"))
        else:
            delivery_type = self.todo.get("source_delivery_type", "other")
            badges.addWidget(self._badge(self._delivery_label(delivery_type), "BadgeNormal"))

        if self.is_overdue:
            badges.addWidget(self._badge("逾期", "BadgeOverdue"))

        badges.addStretch(1)
        root.addLayout(badges)

        status = self.todo.get("status", "open")

        if self.todo.get("is_manual"):
            detail_text = f"具体内容：{self.todo.get('content') or self.todo.get('reason') or '未填写'}"
        else:
            source = self.todo.get("source_subject") or "未知来源邮件"
            reason = self.todo.get("reason") or "未提供生成依据"
            detail_text = f"来源：{source}\n依据：{reason}"

        detail_label = QLabel(detail_text)
        detail_label.setObjectName("TodoReason")
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet(
            """
            QLabel#TodoReason {
                font-size: 16px;
                line-height: 1.75;
                color: #334155;
            }
            """
        )
        root.addWidget(detail_label)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        if status in {"open", "snoozed"}:
            complete = QPushButton("标记完成")
            complete.setObjectName("PrimaryButton")
            complete.clicked.connect(lambda: self._set_status("done"))
            action_row.addWidget(complete)
        elif status == "done":
            reopen = QPushButton("重新打开")
            reopen.setObjectName("SecondaryButton")
            reopen.clicked.connect(lambda: self._set_status("open"))
            action_row.addWidget(reopen)

            delete_btn = QPushButton("删除")
            delete_btn.setObjectName("DeleteTodoButton")
            delete_btn.setStyleSheet(
                """
                QPushButton#DeleteTodoButton {
                    background: #ffffff;
                    border: 1px solid #fecaca;
                    color: #b91c1c;
                    border-radius: 14px;
                    padding: 0px 22px;
                    min-height: 52px;
                    max-height: 52px;
                    font-weight: 800;
                }

                QPushButton#DeleteTodoButton:hover {
                    background: #fef2f2;
                    border: 1px solid #fca5a5;
                }
                """
            )
            delete_btn.clicked.connect(self._delete_todo)
            action_row.addWidget(delete_btn)

        if self.todo.get("is_manual"):
            edit_btn = QPushButton("编辑")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.clicked.connect(self._edit_todo)
            action_row.addWidget(edit_btn)
        else:
            mail_btn = QPushButton("查看邮件正文")
            mail_btn.setObjectName("SecondaryButton")
            mail_btn.clicked.connect(self._open_mail)
            action_row.addWidget(mail_btn)

        self.operation_toggle = QToolButton()
        self.operation_toggle.setAttribute(Qt.WA_OpaquePaintEvent)
        self.operation_toggle.setCheckable(True)
        self.operation_toggle.setChecked(False)
        self.operation_toggle.setArrowType(Qt.RightArrow)
        self.operation_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.operation_toggle.setText("操作")
        self.operation_toggle.setStyleSheet(
            """
            QToolButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 14px;
                padding: 11px 16px;
                font-size: 15px;
                font-weight: 900;
                color: #334155;
                text-align: left;
                min-width: 92px;
            }

            QToolButton:hover {
                background: #f8fafc;
                border: 1px solid #94a3b8;
            }
            """
        )
        self.operation_toggle.clicked.connect(self._toggle_operation_panel)
        action_row.addWidget(self.operation_toggle)
        action_row.addStretch(1)
        root.addLayout(action_row)

        self.operation_panel = QFrame()
        self.operation_panel.setObjectName("OperationPanel")
        self.operation_panel.setVisible(False)
        self.operation_panel.setStyleSheet(
            """
            QFrame#OperationPanel {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
            }

            QFrame#OperationSection {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }

            QLabel#OperationTitle {
                color: #334155;
                font-size: 14px;
                font-weight: 900;
            }

            QLabel#OperationHint {
                color: #64748b;
                font-size: 13px;
            }

            QPushButton#OperationButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                border-radius: 11px;
                padding: 9px 14px;
                font-weight: 800;
            }

            QPushButton#OperationButton:hover {
                background: #f1f5f9;
                border: 1px solid #94a3b8;
            }
            """
        )

        operation_layout = QVBoxLayout(self.operation_panel)
        operation_layout.setContentsMargins(16, 16, 16, 16)
        operation_layout.setSpacing(12)

        attachment_section = QFrame()
        attachment_section.setObjectName("OperationSection")
        attachment_layout = QVBoxLayout(attachment_section)
        attachment_layout.setContentsMargins(14, 14, 14, 14)
        attachment_layout.setSpacing(10)

        attachment_header = QHBoxLayout()
        attachment_title = QLabel(
            f"相关文件（{len(self.todo.get('attachments', []))}）"
        )
        attachment_title.setObjectName("OperationTitle")
        attachment_header.addWidget(attachment_title)
        attachment_header.addStretch(1)

        upload_btn = QPushButton("上传文件")
        upload_btn.setObjectName("OperationButton")
        upload_btn.clicked.connect(self._upload_attachments)
        attachment_header.addWidget(upload_btn)
        attachment_layout.addLayout(attachment_header)

        attachments = self.todo.get("attachments", [])

        if not attachments:
            empty = QLabel("暂无附件，可点击右上角上传。")
            empty.setObjectName("OperationHint")
            attachment_layout.addWidget(empty)
        else:
            for attachment in attachments:
                row = AttachmentRow(attachment)
                row.delete_requested.connect(self._delete_attachment)
                attachment_layout.addWidget(row)

        operation_layout.addWidget(attachment_section)

        self._stage_section = QFrame()
        self._stage_section.setObjectName("OperationSection")
        stage_layout = QVBoxLayout(self._stage_section)
        stage_layout.setContentsMargins(14, 14, 14, 14)
        stage_layout.setSpacing(10)

        stage_header = QHBoxLayout()
        self._stage_title = QLabel(
            f"阶段完成情况（{len(self.todo.get('stages', []))}）"
        )
        self._stage_title.setObjectName("OperationTitle")
        stage_header.addWidget(self._stage_title)
        stage_header.addStretch(1)
        stage_layout.addLayout(stage_header)

        self._stage_body_widget = QWidget()
        self._stage_body_layout = QVBoxLayout(self._stage_body_widget)
        self._stage_body_layout.setContentsMargins(0, 0, 0, 0)
        self._stage_body_layout.setSpacing(10)
        stage_layout.addWidget(self._stage_body_widget)
        self._populate_stage_rows()

        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self._stage_edit = QLineEdit()
        self._stage_edit.setPlaceholderText("输入阶段描述...")
        self._stage_edit.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        self._stage_edit.returnPressed.connect(self._add_stage)
        add_row.addWidget(self._stage_edit, 1)

        self._stage_deadline_value = None
        self._stage_deadline_btn = QPushButton("截止")
        self._stage_deadline_btn.setObjectName("OperationButton")
        self._stage_deadline_btn.clicked.connect(self._pick_stage_deadline)
        self._stage_deadline_btn.setStyleSheet("""
            QPushButton#OperationButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton#OperationButton:hover {
                background: #f1f5f9;
                border: 1px solid #94a3b8;
            }
        """)
        add_row.addWidget(self._stage_deadline_btn, 0, Qt.AlignVCenter)

        add_stage_btn = QPushButton("添加")
        add_stage_btn.setObjectName("OperationButton")
        add_stage_btn.clicked.connect(self._add_stage)
        add_row.addWidget(add_stage_btn, 0, Qt.AlignVCenter)

        stage_layout.addLayout(add_row)
        operation_layout.addWidget(self._stage_section)
        root.addWidget(self.operation_panel)

    def _populate_stage_rows(self):
        while self._stage_body_layout.count():
            item = self._stage_body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        stages = self.todo.get("stages", [])
        if not stages:
            empty = QLabel("暂无阶段，可在下方添加。")
            empty.setObjectName("OperationHint")
            self._stage_body_layout.addWidget(empty)
        else:
            for stage in stages:
                row = StageRow(stage)
                row.status_changed.connect(self._toggle_stage_status)
                row.delete_requested.connect(self._delete_stage)
                self._stage_body_layout.addWidget(row)

        count = len(stages)
        self._stage_title.setText(f"阶段完成情况（{count}）")

    def _deadline_button_text(self):
        deadline = self.todo.get("deadline")
        if deadline:
            return f"截止：{deadline}  ✎"
        return "截止：无明确截止时间  ✎"

    def _delivery_label(self, delivery_type: str) -> str:
        mapping = {
            "direct": "直发",
            "cc": "抄送",
            "other": "其他",
            "manual": "人工",
        }
        return mapping.get(delivery_type, "其他")

    def _set_status(self, status: str):
        try:
            update_status(self.todo["id"], status)
            self.changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "状态更新失败", str(exc))

    def _delete_todo(self):
        confirm = QMessageBox.question(
            self,
            "确认删除",
            f"确定永久删除待办「{self.todo.get('title', '')}」吗？\n附件也会一并删除，此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            delete_todo(self.todo["id"])
            self.changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", str(exc))

    def _show_priority_menu(self):
        self._priority_menu.exec(self.priority_btn.mapToGlobal(
            self.priority_btn.rect().bottomLeft()
        ))

    def _change_priority(self, value: str):
        try:
            update_priority(self.todo["id"], value)
            self.todo["priority"] = value
            self.priority_btn.setText(PRIORITY_LABELS.get(value, value))
            self.priority_btn.setObjectName(PRIORITY_OBJECTS.get(value, "BadgeNormal"))
            self.priority_btn.style().unpolish(self.priority_btn)
            self.priority_btn.style().polish(self.priority_btn)
        except Exception as exc:
            QMessageBox.critical(self, "优先级更新失败", str(exc))

    def _edit_deadline(self):
        dialog = DeadlineEditDialog(self.todo.get("deadline"), self)

        if not dialog.exec():
            return

        try:
            update_deadline(self.todo["id"], dialog.deadline_value)
            QMessageBox.information(self, "保存成功", "截止时间已更新。")
            self.changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "截止时间更新失败", str(exc))

    def _edit_todo(self):
        from client.widgets.manual_todo_dialog import ManualTodoDialog
        dialog = ManualTodoDialog(todo=self.todo, parent=self)
        if dialog.exec():
            self.changed.emit()

    def _open_mail(self):
        dialog = MailDetailDialog(self.todo, self)
        dialog.exec()

    def _toggle_operation_panel(self, checked: bool):
        self.setUpdatesEnabled(False)
        self.operation_panel.setVisible(checked)
        self.operation_toggle.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )
        self.setUpdatesEnabled(True)

    def _upload_attachments(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择待办相关文件",
            str(Path.home()),
            "所有文件 (*.*)"
        )

        if not paths:
            return

        success_count = 0

        try:
            for file_path in paths:
                path = Path(file_path)
                add_todo_attachment(
                    self.todo["id"],
                    path.name,
                    path.read_bytes()
                )
                success_count += 1

            QMessageBox.information(
                self,
                "上传成功",
                f"已上传 {success_count} 个文件。"
            )
            self.changed.emit()

        except Exception as exc:
            QMessageBox.critical(self, "上传失败", str(exc))

    def _delete_attachment(self, attachment_path: str):
        confirm = QMessageBox.question(
            self,
            "确认删除附件",
            "确定删除该附件吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            delete_todo_attachment(
                self.todo["id"],
                attachment_path
            )
            QMessageBox.information(self, "删除成功", "附件已删除。")
            self.changed.emit()

        except Exception as exc:
            QMessageBox.critical(self, "删除失败", str(exc))

    def _toggle_stage_status(self, stage_id: int, new_status: str):
        try:
            updated = update_stage_status(stage_id, new_status)
            for i, s in enumerate(self.todo.get("stages", [])):
                if s["id"] == stage_id:
                    self.todo["stages"][i] = updated
                    break
            self._populate_stage_rows()
        except Exception as exc:
            QMessageBox.critical(self, "阶段状态更新失败", str(exc))

    def _delete_stage(self, stage_id: int):
        try:
            delete_stage(stage_id)
            self.todo["stages"] = [
                s for s in self.todo.get("stages", [])
                if s["id"] != stage_id
            ]
            self._populate_stage_rows()
        except Exception as exc:
            QMessageBox.critical(self, "阶段删除失败", str(exc))

    def _pick_stage_deadline(self):
        from PySide6.QtWidgets import QInputDialog

        initial = self._stage_deadline_value or QDate.currentDate().toString("yyyy-MM-dd")
        text, ok = QInputDialog.getText(
            self, "阶段截止时间", "请输入截止日期（YYYY-MM-DD）：", text=initial
        )
        if ok and text.strip():
            self._stage_deadline_value = text.strip()
            self._stage_deadline_btn.setText(f"截止：{self._stage_deadline_value}")
        elif ok:
            self._stage_deadline_value = None
            self._stage_deadline_btn.setText("截止")

    def _add_stage(self):
        title = self._stage_edit.text().strip()
        if not title:
            QMessageBox.information(self, "提示", "请输入阶段描述。")
            return

        try:
            new_stage = add_stage(
                todo_id=self.todo["id"],
                title=title,
                deadline=self._stage_deadline_value,
            )
            self.todo.setdefault("stages", []).append(new_stage)
            self._stage_edit.clear()
            self._stage_deadline_value = None
            self._stage_deadline_btn.setText("截止")
            self._populate_stage_rows()
        except Exception as exc:
            QMessageBox.critical(self, "阶段添加失败", str(exc))
