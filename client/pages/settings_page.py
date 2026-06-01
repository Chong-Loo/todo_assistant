from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QMessageBox,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QAbstractSpinBox,
    QSizePolicy,
    QScrollArea,
)

from app.settings import (
    delete_llm_profile,
    get_llm_token,
    get_llm_profile_token,
    get_mail_password,
    list_llm_profiles,
    load_config,
    load_user_config,
    save_llm_profile,
    save_mail_password,
    update_user_config,
)


class EditableModelComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setFrame(False)
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            """
            QComboBox {
                background: transparent;
                border: none;
                padding: 0px;
                color: #1f2937;
            }

            QComboBox::drop-down {
                border: none;
                width: 42px;
            }

            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }

            QComboBox QLineEdit {
                background: transparent;
                border: none;
                padding: 0px 44px 0px 14px;
                color: #1f2937;
            }

            QComboBox QAbstractItemView {
                background: #ffffff;
                color: #1f2937;
                border: 1px solid #cbd5e1;
                selection-background-color: #dbeafe;
                selection-color: #1d4ed8;
                outline: 0;
            }
            """
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(0.75, 0.75, self.width() - 1.5, self.height() - 1.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        border = QColor("#2563eb") if self.hasFocus() else QColor("#cbd5e1")
        painter.fillPath(path, QColor("#ffffff"))
        painter.setPen(QPen(border, 1.2))
        painter.drawPath(path)

        separator_x = self.width() - 42
        painter.setPen(QPen(QColor("#e2e8f0"), 1.0))
        painter.drawLine(separator_x, 8, separator_x, self.height() - 8)

        cx = self.width() - 21
        cy = self.height() / 2 + 1
        chevron = QPainterPath()
        chevron.moveTo(cx - 6, cy - 3)
        chevron.lineTo(cx, cy + 3)
        chevron.lineTo(cx + 6, cy - 3)
        painter.setPen(QPen(QColor("#64748b"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(chevron)

        if not self.isEditable():
            text_rect = QRectF(14, 0, max(0, self.width() - 62), self.height())
            painter.setPen(QColor("#1f2937") if self.isEnabled() else QColor("#94a3b8"))
            painter.drawText(
                text_rect,
                int(Qt.AlignVCenter | Qt.AlignLeft),
                self.currentText(),
            )

        painter.end()


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.reload()

    def _build_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        content = QWidget()
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        title = QLabel("设置")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        hint = QLabel("邮箱密码和大模型 Token 将保存到系统 keyring。")
        hint.setObjectName("SectionHint")
        root.addWidget(hint)

        mail_panel = QFrame()
        mail_panel.setObjectName("PanelCard")
        mail_layout = QVBoxLayout(mail_panel)
        mail_layout.setContentsMargins(20, 18, 20, 18)
        mail_layout.setSpacing(10)

        mail_title = QLabel("邮箱账号")
        mail_title.setObjectName("SectionTitle")
        mail_layout.addWidget(mail_title)

        self.mail_host_input = QLineEdit()
        self.mail_port_input = QSpinBox()
        self.mail_port_input.setRange(1, 65535)
        self.mail_port_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.mail_username_input = QLineEdit()
        self.mail_password_input = QLineEdit()
        self.mail_password_input.setEchoMode(QLineEdit.Password)
        self.mail_password_input.setPlaceholderText("留空则不修改已保存密码")
        self.mail_folder_input = QLineEdit()
        self.mail_ssl_check = QCheckBox("使用 SSL")

        for field in (
            self.mail_host_input,
            self.mail_port_input,
            self.mail_username_input,
            self.mail_password_input,
            self.mail_folder_input,
        ):
            self._normalize_field(field)

        mail_layout.addWidget(self._form_row("IMAP 服务器", self.mail_host_input))
        mail_layout.addWidget(self._form_row("端口", self.mail_port_input))
        mail_layout.addWidget(self._form_row("邮箱账号", self.mail_username_input))
        mail_layout.addWidget(self._form_row("邮箱密码", self.mail_password_input))
        mail_layout.addWidget(self._form_row("邮箱目录", self.mail_folder_input))
        mail_layout.addWidget(self._form_row("", self.mail_ssl_check, compact=True))
        root.addWidget(mail_panel)

        llm_panel = QFrame()
        llm_panel.setObjectName("PanelCard")
        llm_layout = QVBoxLayout(llm_panel)
        llm_layout.setContentsMargins(20, 18, 20, 18)
        llm_layout.setSpacing(10)

        llm_title = QLabel("模型配置")
        llm_title.setObjectName("SectionTitle")
        llm_layout.addWidget(llm_title)

        llm_warning = QLabel(
            "注意：分析公司邮箱待办时一定要使用公司内网模型，"
            "使用外网模型数据泄露后果自负！"
        )
        llm_warning.setWordWrap(True)
        llm_warning.setStyleSheet(
            """
            QLabel {
                background: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 10px;
                padding: 10px 12px;
                font-weight: 900;
            }
            """
        )
        llm_layout.addWidget(llm_warning)

        self.llm_profiles: list[dict] = []
        self.llm_profile_combo = EditableModelComboBox()
        self.llm_profile_combo.setEditable(False)
        self.llm_profile_combo.currentIndexChanged.connect(self._select_llm_profile)

        delete_profile_btn = QPushButton("删除")
        delete_profile_btn.setObjectName("CompactDangerButton")
        delete_profile_btn.setFixedSize(82, 42)
        delete_profile_btn.setStyleSheet(
            """
            QPushButton#CompactDangerButton {
                background: #ffffff;
                border: 1px solid #fecaca;
                color: #991b1b;
                border-radius: 10px;
                font-weight: 900;
            }

            QPushButton#CompactDangerButton:hover {
                background: #fef2f2;
                border: 1px solid #fca5a5;
            }
            """
        )
        delete_profile_btn.clicked.connect(self._delete_llm_profile)

        profile_row = QWidget()
        profile_row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        profile_row.setMinimumHeight(54)
        profile_row.setMaximumHeight(54)

        profile_layout = QHBoxLayout(profile_row)
        profile_layout.setContentsMargins(0, 3, 0, 3)
        profile_layout.setSpacing(18)
        profile_layout.addWidget(self._form_label("历史配置", 48))
        profile_layout.addWidget(self.llm_profile_combo, 1, Qt.AlignVCenter)
        profile_layout.addWidget(delete_profile_btn, 0, Qt.AlignVCenter)
        llm_layout.addWidget(profile_row)

        self.llm_endpoint_input = QLineEdit()
        self.llm_model_input = QLineEdit()

        self.llm_token_input = QLineEdit()
        self.llm_token_input.setEchoMode(QLineEdit.Password)
        self.llm_token_input.setPlaceholderText("留空则不修改已保存 Token")

        self.llm_timeout_input = QSpinBox()
        self.llm_timeout_input.setRange(5, 600)
        self.llm_timeout_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.llm_timeout_input.setSuffix(" 秒")

        for field in (
            self.llm_endpoint_input,
            self.llm_model_input,
            self.llm_token_input,
            self.llm_timeout_input,
        ):
            self._normalize_field(field)

        llm_layout.addWidget(self._form_row("接口地址", self.llm_endpoint_input))
        llm_layout.addWidget(self._form_row("模型名称", self.llm_model_input))
        llm_layout.addWidget(self._form_row("Token", self.llm_token_input))
        llm_layout.addWidget(self._form_row("超时时间", self.llm_timeout_input))
        root.addWidget(llm_panel)

        actions = QHBoxLayout()
        actions.addStretch(1)

        reload_btn = QPushButton("重新载入")
        reload_btn.setObjectName("SecondaryButton")
        reload_btn.clicked.connect(self.reload)
        actions.addWidget(reload_btn)

        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save)
        actions.addWidget(save_btn)

        root.addLayout(actions)
        root.addStretch(1)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)

    def _form_label(self, text: str, height: int = 54) -> QLabel:
        label = QLabel(text)
        label.setFixedWidth(150)
        label.setMinimumHeight(height)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        return label

    def _normalize_field(self, field):
        field.setMinimumHeight(48)
        field.setMaximumHeight(48)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _form_row(self, label_text: str, field, compact: bool = False) -> QWidget:
        row_widget = QWidget()
        row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_widget.setMinimumHeight(38 if compact else 54)
        row_widget.setMaximumHeight(38 if compact else 54)

        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 3, 0, 3)
        row.setSpacing(18)
        row.addWidget(self._form_label(label_text, 32 if compact else 48))
        row.addWidget(field, 1, Qt.AlignVCenter)

        return row_widget

    def reload(self):
        config = load_config()
        user_config = load_user_config()
        mail_cfg = config.get("mail", {})
        llm_cfg = user_config.get("llm", {})
        if not isinstance(llm_cfg, dict):
            llm_cfg = {}

        self.mail_host_input.setText(str(mail_cfg.get("host", "")))
        self.mail_port_input.setValue(int(mail_cfg.get("port", 993)))
        self.mail_username_input.setText(str(mail_cfg.get("username", "")))
        self.mail_folder_input.setText(str(mail_cfg.get("folder", "INBOX")))
        self.mail_ssl_check.setChecked(bool(mail_cfg.get("use_ssl", True)))
        self.mail_password_input.clear()

        if get_mail_password(str(mail_cfg.get("username", ""))):
            self.mail_password_input.setPlaceholderText("已保存，留空则不修改")
        else:
            self.mail_password_input.setPlaceholderText("请输入邮箱密码")

        self._reload_llm_profiles(llm_cfg)

        self.llm_endpoint_input.setText(str(llm_cfg.get("endpoint", "")))
        model = str(llm_cfg.get("model", ""))
        self.llm_model_input.setText(model)

        self.llm_timeout_input.setValue(int(llm_cfg.get("timeout", 60)))
        self.llm_token_input.clear()

        token_account = str(llm_cfg.get("token_account", "")).strip()
        if get_llm_profile_token(token_account) or get_llm_token():
            self.llm_token_input.setPlaceholderText("已保存，留空则不修改")
        else:
            self.llm_token_input.setPlaceholderText("请输入大模型 Token")

    def _reload_llm_profiles(self, llm_cfg: dict):
        self.llm_profile_combo.blockSignals(True)

        self.llm_profiles = list_llm_profiles()
        self.llm_profile_combo.clear()

        if not self.llm_profiles:
            self.llm_profile_combo.addItem("暂无历史配置", "")
        else:
            for profile in self.llm_profiles:
                model = str(profile.get("model", "")).strip()
                endpoint = str(profile.get("endpoint", "")).strip()
                token_account = str(profile.get("token_account", "")).strip()

                self.llm_profile_combo.addItem(
                    f"{model}  |  {endpoint}",
                    token_account,
                )

        current_account = str(llm_cfg.get("token_account", "")).strip()
        current_index = self.llm_profile_combo.findData(current_account)
        if current_index >= 0:
            self.llm_profile_combo.setCurrentIndex(current_index)
        else:
            self.llm_profile_combo.setCurrentIndex(0)

        self.llm_profile_combo.blockSignals(False)

    def _save(self):
        username = self.mail_username_input.text().strip()
        mail_password = self.mail_password_input.text()
        llm_token = self.llm_token_input.text()

        if not username:
            QMessageBox.warning(self, "提示", "邮箱账号不能为空。")
            return

        model = self.llm_model_input.text().strip()
        if not model:
            QMessageBox.warning(self, "提示", "大模型名称不能为空。")
            return

        endpoint = self.llm_endpoint_input.text().strip()
        if not endpoint:
            QMessageBox.warning(self, "提示", "接口地址不能为空。")
            return

        try:
            update_user_config(
                "mail",
                {
                    "host": self.mail_host_input.text().strip(),
                    "port": self.mail_port_input.value(),
                    "username": username,
                    "use_ssl": self.mail_ssl_check.isChecked(),
                    "folder": self.mail_folder_input.text().strip() or "INBOX",
                },
            )
            if mail_password:
                save_mail_password(username, mail_password)

            save_llm_profile(
                model=model,
                endpoint=endpoint,
                timeout=self.llm_timeout_input.value(),
                token=llm_token or None,
            )

            QMessageBox.information(self, "保存成功", "设置已保存。")
            self.reload()

        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))

    def _select_llm_profile(self):
        token_account = str(self.llm_profile_combo.currentData() or "")
        if not token_account:
            return

        profile = next(
            (
                item for item in self.llm_profiles
                if item.get("token_account") == token_account
            ),
            None,
        )
        if not profile:
            return

        self.llm_endpoint_input.setText(str(profile.get("endpoint", "")))
        self.llm_model_input.setText(str(profile.get("model", "")))
        self.llm_timeout_input.setValue(int(profile.get("timeout", 60) or 60))
        self.llm_token_input.clear()

        if get_llm_profile_token(token_account):
            self.llm_token_input.setPlaceholderText("已保存，留空则不修改")
        else:
            self.llm_token_input.setPlaceholderText("请输入大模型 Token")

    def _delete_llm_profile(self):
        token_account = str(self.llm_profile_combo.currentData() or "")
        if not token_account:
            QMessageBox.information(self, "提示", "没有可删除的历史配置。")
            return

        confirm = QMessageBox.question(
            self,
            "确认删除",
            "确定删除当前模型历史配置吗？对应 Token 也会从 keyring 中删除。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            delete_llm_profile(token_account)
            self.reload()
            QMessageBox.information(self, "删除成功", "模型历史配置已删除。")
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", str(exc))
