from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.email_tracker import clear_tracking, delete_fetched_email, list_fetched_emails


class FetchedEmailsDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查看拉取记录")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setModal(True)

        self._username = username
        self._build_ui()
        self._load_data()
        self.resize(1100, 700)
        self.showMaximized()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title_row = QHBoxLayout()
        title_label = QLabel("邮件拉取记录")
        title_label.setObjectName("PopupTitle")
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        root.addLayout(title_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["", "主题", "发件人", "邮件日期", "拉取时间", "邮箱", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 60)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.select_all_cb = QCheckBox("全选")
        self.select_all_cb.toggled.connect(self._toggle_select_all)
        btn_row.addWidget(self.select_all_cb)

        self.delete_selected_btn = QPushButton("删除选中")
        self.delete_selected_btn.setObjectName("CompactDangerButton")
        self.delete_selected_btn.setMinimumHeight(36)
        self.delete_selected_btn.setStyleSheet("padding: 0px 22px;")
        self.delete_selected_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.delete_selected_btn)

        btn_row.addStretch(1)

        self.clear_all_btn = QPushButton("清空拉取记录")
        self.clear_all_btn.setObjectName("DangerButton")
        self.clear_all_btn.setMinimumHeight(44)
        self.clear_all_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(self.clear_all_btn)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("SecondaryButton")
        close_btn.setMinimumHeight(44)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    def _load_data(self):
        records = list_fetched_emails(self._username)
        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            subject = rec.get("subject") or "(无主题)"
            from_addr = rec.get("from_addr") or ""
            mail_date = rec.get("date") or ""
            fetched_at_raw = rec.get("fetched_at") or ""
            mailbox = rec.get("mailbox") or ""

            try:
                dt = datetime.fromisoformat(fetched_at_raw)
                fetched_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                fetched_at = fetched_at_raw

            cb = QCheckBox()
            cw = QWidget()
            cl = QHBoxLayout(cw)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(Qt.AlignCenter)
            cl.addWidget(cb)
            self.table.setCellWidget(row, 0, cw)

            subject_item = QTableWidgetItem(subject)
            subject_item.setData(Qt.UserRole, rec["id"])
            self.table.setItem(row, 1, subject_item)
            self.table.setItem(row, 2, QTableWidgetItem(from_addr))
            self.table.setItem(row, 3, QTableWidgetItem(mail_date))
            self.table.setItem(row, 4, QTableWidgetItem(fetched_at))
            self.table.setItem(row, 5, QTableWidgetItem(mailbox))

            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #3b82f6;
                    text-decoration: underline;
                    font-weight: 800;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: #1d4ed8;
                }
            """)
            record_id = rec["id"]
            del_btn.clicked.connect(lambda checked, rid=record_id, r=row: self._delete_row(rid, r))
            self.table.setCellWidget(row, 6, del_btn)

    def _toggle_select_all(self, checked: bool):
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb:
                    cb.setChecked(checked)

    def _record_id_at(self, row: int) -> int | None:
        item = self.table.item(row, 1)
        if item:
            return item.data(Qt.UserRole)
        return None

    def _get_selected_ids(self) -> list[tuple[int, int]]:
        selected = []
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb and cb.isChecked():
                    rid = self._record_id_at(row)
                    if rid is not None:
                        selected.append((row, rid))
        return selected

    def _delete_selected(self):
        selected = self._get_selected_ids()
        if not selected:
            QMessageBox.information(self, "提示", "请先勾选要删除的记录。")
            return
        confirm = QMessageBox.question(
            self,
            "确认批量删除",
            f"确定删除选中的 {len(selected)} 条记录吗？\n删除后，下次分析将重新拉取这些邮件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        for row, rid in sorted(selected, reverse=True):
            try:
                delete_fetched_email(rid)
                self.table.removeRow(row)
            except Exception as exc:
                QMessageBox.critical(self, "删除失败", str(exc))

    def _delete_row(self, record_id: int, row: int):
        confirm = QMessageBox.question(
            self,
            "确认删除",
            "删除后，下次分析将重新拉取该邮件。\n确定继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            delete_fetched_email(record_id)
            self.table.removeRow(row)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", str(exc))

    def _clear_all(self):
        confirm = QMessageBox.question(
            self,
            "确认操作",
            "清空邮件拉取记录后，下次分析会重新拉取所有邮件。\n确定继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            clear_tracking(self._username)
            self.table.setRowCount(0)
            QMessageBox.information(self, "操作完成", "邮件拉取记录已清空。")
        except Exception as exc:
            QMessageBox.critical(self, "操作失败", str(exc))
