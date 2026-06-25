from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.image_processor import extract_todos_from_image
from app.todo_manager import add_manual_todo, add_todo_attachment
from client.widgets.manual_todo_dialog import ManualTodoDialog


SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"}


class ImageTodoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片识别待办")
        self.resize(640, 560)
        self.setModal(True)
        self.setAcceptDrops(True)

        self.image_path: str | None = None

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QPushButton#DropZone {
                border: 2px dashed #94a3b8;
                border-radius: 16px;
                background: #f8fafc;
                font-size: 15px;
                color: #64748b;
                padding: 40px;
            }
            QPushButton#DropZone:hover {
                border-color: #3b82f6;
                background: #eff6ff;
                color: #3b82f6;
            }
            QPushButton#DropZone.drag-over {
                border-color: #22c55e;
                background: #f0fdf4;
                color: #22c55e;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(16)

        title = QLabel("图片识别生成待办")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(280)
        self.preview_label.setStyleSheet(
            "background: #f1f5f9; border-radius: 12px; color: #94a3b8; font-size: 14px;"
        )
        self._set_placeholder()
        root.addWidget(self.preview_label, 1)

        action_bar = QHBoxLayout()

        self.pick_button = QPushButton("选择图片")
        self.pick_button.setObjectName("PrimaryButton")
        self.pick_button.clicked.connect(self._pick_image)
        action_bar.addWidget(self.pick_button)

        action_bar.addStretch()

        self.recognize_button = QPushButton("识别待办")
        self.recognize_button.setObjectName("PrimaryButton")
        self.recognize_button.clicked.connect(self._recognize)
        self.recognize_button.setEnabled(False)
        action_bar.addWidget(self.recognize_button)

        root.addLayout(action_bar)

    def _set_placeholder(self):
        self.preview_label.setText("拖拽图片到此处\n或点击下方「选择图片」\n支持 Ctrl+V 粘贴截图")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in SUPPORTED_FORMATS:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in SUPPORTED_FORMATS:
                self._load_image(path)
                event.acceptProposedAction()
                return

    def keyPressEvent(self, event: QKeyEvent):
        if event.matches(QKeySequence.Paste):
            clipboard = QApplication.clipboard()
            image = clipboard.image()
            if not image.isNull():
                tmp = Path(tempfile.gettempdir()) / "todo_assistant_paste.png"
                image.save(str(tmp))
                self._load_image(str(tmp))
                return
        super().keyPressEvent(event)

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片",
            str(Path.home()),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif)"
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str):
        self.image_path = path
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "提示", "无法加载图片，请检查文件格式。")
            return
        scaled = pixmap.scaled(
            self.preview_label.width(), 400,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)
        self.recognize_button.setEnabled(True)

    def _recognize(self):
        if not self.image_path:
            return

        self.recognize_button.setEnabled(False)
        self.recognize_button.setText("识别中...")
        QApplication.processEvents()

        try:
            result = extract_todos_from_image(self.image_path)
            todos = result.get("todos", [])
            if not todos:
                QMessageBox.information(self, "识别结果", "未从图片中识别到待办事项。")
                return

            todo = todos[0]
            dialog = ManualTodoDialog(parent=self)
            dialog.setWindowTitle("确认待办")
            dialog.title_input.setText(todo.get("title", ""))
            priority = todo.get("priority", "normal")
            idx = dialog.priority_combo.findData(priority)
            if idx >= 0:
                dialog.priority_combo.setCurrentIndex(idx)
            if todo.get("deadline"):
                dialog.deadline_value = todo["deadline"]
                dialog.deadline_button.setText(dialog._deadline_button_text())
            content_parts = []
            if todo.get("content"):
                content_parts.append(todo["content"])
            if todo.get("reason"):
                content_parts.append(f"[依据] {todo['reason']}")
            dialog.content_input.setPlainText("\n\n".join(content_parts) if content_parts else "")
            dialog.file_paths = [self.image_path]
            dialog.file_list.addItem(QListWidgetItem(Path(self.image_path).name))

            if dialog.exec():
                self._save_with_attachment(
                    dialog,
                    dialog.title_input.text().strip(),
                    dialog.priority_combo.currentData(),
                    dialog.deadline_value,
                    dialog.content_input.toPlainText().strip(),
                    dialog.note_input.toPlainText().strip(),
                )
        except Exception as e:
            QMessageBox.critical(self, "识别失败", f"图片识别出错：{str(e)}")
        finally:
            self.recognize_button.setEnabled(True)
            self.recognize_button.setText("识别待办")

    def _save_with_attachment(self, dialog, title, priority, deadline, content, note):
        try:
            todo = add_manual_todo(
                title=title, priority=priority,
                deadline=deadline, content=content, note=note
            )
            for file_path in dialog.file_paths:
                path = Path(file_path)
                add_todo_attachment(todo["id"], path.name, path.read_bytes())
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
