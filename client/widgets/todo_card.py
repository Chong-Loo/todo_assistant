from __future__ import annotations

from pathlib import Path
import os
import sys
import subprocess

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QToolButton,
)

from app.todo_manager import (
    update_priority,
    update_status,
    update_deadline,
    add_todo_attachment,
    delete_todo_attachment,
)
from app.todo_status import is_todo_overdue
from client.widgets.deadline_dialog import DeadlineEditDialog
from client.widgets.mail_detail_dialog import MailDetailDialog
from client.widgets.painted_combo_box import PaintedComboBox


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


class TodoCard(QFrame):
    changed = Signal()

    def __init__(self, todo: dict, parent=None):
        super().__init__(parent)
        self.todo = todo
        self.is_overdue = is_todo_overdue(todo)
        self.setObjectName("TodoCard")
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

        priority = self.todo.get("priority", "normal")
        badges.addWidget(
            self._badge(
                PRIORITY_LABELS.get(priority, priority),
                PRIORITY_OBJECTS.get(priority, "BadgeNormal")
            )
        )

        status = self.todo.get("status", "open")
        badges.addWidget(
            self._badge(
                STATUS_LABELS.get(status, status),
                STATUS_OBJECTS.get(status, "BadgeOpen")
            )
        )

        if self.todo.get("is_manual"):
            badges.addWidget(self._badge("人工", "BadgeNormal"))
        else:
            delivery_type = self.todo.get("source_delivery_type", "other")
            badges.addWidget(self._badge(self._delivery_label(delivery_type), "BadgeNormal"))

        if self.is_overdue:
            badges.addWidget(self._badge("逾期", "BadgeOverdue"))

        badges.addStretch(1)
        root.addLayout(badges)

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

        if not self.todo.get("is_manual"):
            mail_btn = QPushButton("查看邮件正文")
            mail_btn.setObjectName("SecondaryButton")
            mail_btn.clicked.connect(self._open_mail)
            action_row.addWidget(mail_btn)

        self.operation_toggle = QToolButton()
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

        priority_section = QFrame()
        priority_section.setObjectName("OperationSection")
        priority_layout = QVBoxLayout(priority_section)
        priority_layout.setContentsMargins(14, 14, 14, 14)
        priority_layout.setSpacing(10)

        priority_title = QLabel("调整优先级")
        priority_title.setObjectName("OperationTitle")
        priority_layout.addWidget(priority_title)

        priority_row = QHBoxLayout()
        priority_row.setSpacing(10)

        self.priority_combo = PaintedComboBox()
        for label, value in PRIORITY_OPTIONS:
            self.priority_combo.addItem(label, value)

        current_priority = self.todo.get("priority", "normal")
        index = max(0, self.priority_combo.findData(current_priority))
        self.priority_combo.setCurrentIndex(index)
        priority_row.addWidget(self.priority_combo)

        save_priority_btn = QPushButton("保存")
        save_priority_btn.setObjectName("OperationButton")
        save_priority_btn.clicked.connect(self._save_priority)
        priority_row.addWidget(save_priority_btn)
        priority_row.addStretch(1)

        priority_layout.addLayout(priority_row)
        operation_layout.addWidget(priority_section)

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
        root.addWidget(self.operation_panel)

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

    def _save_priority(self):
        try:
            update_priority(
                self.todo["id"],
                self.priority_combo.currentData()
            )
            QMessageBox.information(self, "保存成功", "优先级已更新。")
            self.changed.emit()
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

    def _open_mail(self):
        dialog = MailDetailDialog(self.todo, self)
        dialog.exec()

    def _toggle_operation_panel(self, checked: bool):
        self.operation_panel.setVisible(checked)
        self.operation_toggle.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )

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
