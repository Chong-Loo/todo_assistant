from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPalette
from PySide6.QtWidgets import (
    QApplication,
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
    QStackedWidget,
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
from client.styles import set_app_stylesheet


class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


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

    def _is_dark_mode(self):
        app = QApplication.instance()
        palette = app.palette()
        c = palette.color(QPalette.Window)
        return c.lightness() < 128

    def paintEvent(self, event):
        is_dark = self._is_dark_mode()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(0.75, 0.75, self.width() - 1.5, self.height() - 1.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        if is_dark:
            bg = QColor("#1e293b")
            border_focus = QColor("#3b82f6")
            border_normal = QColor("#475569")
            separator = QColor("#475569")
            chevron = QColor("#94a3b8")
            text = QColor("#f1f5f9") if self.isEnabled() else QColor("#64748b")
        else:
            bg = QColor("#ffffff")
            border_focus = QColor("#2563eb")
            border_normal = QColor("#cbd5e1")
            separator = QColor("#e2e8f0")
            chevron = QColor("#64748b")
            text = QColor("#1f2937") if self.isEnabled() else QColor("#94a3b8")

        border = border_focus if self.hasFocus() else border_normal
        painter.fillPath(path, bg)
        painter.setPen(QPen(border, 1.2))
        painter.drawPath(path)

        separator_x = self.width() - 42
        painter.setPen(QPen(separator, 1.0))
        painter.drawLine(separator_x, 8, separator_x, self.height() - 8)

        cx = self.width() - 21
        cy = self.height() / 2 + 1
        chevron_path = QPainterPath()
        chevron_path.moveTo(cx - 6, cy - 3)
        chevron_path.lineTo(cx, cy + 3)
        chevron_path.lineTo(cx + 6, cy - 3)
        painter.setPen(QPen(chevron, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(chevron_path)

        if not self.isEditable():
            text_rect = QRectF(14, 0, max(0, self.width() - 62), self.height())
            painter.setPen(text)
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
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # left navigation
        nav = QFrame()
        nav.setFixedWidth(180)
        nav.setObjectName("SettingsNav")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)

        self.nav_buttons = []
        nav_items = ["📮 邮箱账号", "🤖 模型配置", "⚙️ 应用设置"]
        for i, text in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setObjectName("SettingsNavButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, idx=i: self._switch_nav(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            if i == 0:
                btn.setChecked(True)

        nav_layout.addStretch(1)
        root.addWidget(nav)

        # content stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("SettingsStack")

        # page 0 - mail
        mail_content = QWidget()
        mail_content.setObjectName("SettingsContent")
        mail_scroll = QScrollArea()
        mail_scroll.setWidgetResizable(True)
        mail_scroll.setFrameShape(QFrame.NoFrame)
        mail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        mail_root = QVBoxLayout(mail_content)
        mail_root.setContentsMargins(26, 22, 26, 22)
        mail_root.setSpacing(16)

        mail_title = QLabel("📮 邮箱账号")
        mail_title.setObjectName("SectionTitle")
        mail_root.addWidget(mail_title)

        mail_panel = QFrame()
        mail_panel.setObjectName("PanelCard")
        mail_layout = QVBoxLayout(mail_panel)
        mail_layout.setContentsMargins(20, 18, 20, 18)
        mail_layout.setSpacing(10)

        self.mail_host_input = QLineEdit()
        self.mail_port_input = NoWheelSpinBox()
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
        mail_root.addWidget(mail_panel)

        mail_root.addStretch(1)
        mail_scroll.setWidget(mail_content)
        self.stack.addWidget(mail_scroll)

        # page 1 - llm
        llm_content = QWidget()
        llm_content.setObjectName("SettingsContent")
        llm_scroll = QScrollArea()
        llm_scroll.setWidgetResizable(True)
        llm_scroll.setFrameShape(QFrame.NoFrame)
        llm_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        llm_root = QVBoxLayout(llm_content)
        llm_root.setContentsMargins(26, 22, 26, 22)
        llm_root.setSpacing(16)

        llm_title = QLabel("🤖 模型配置")
        llm_title.setObjectName("SectionTitle")
        llm_root.addWidget(llm_title)

        llm_warning = QLabel(
            "注意：分析公司邮箱待办时一定要使用公司内网模型，"
            "使用外网模型数据泄露后果自负！"
        )
        llm_warning.setObjectName("LlmWarning")
        llm_warning.setWordWrap(True)
        llm_root.addWidget(llm_warning)

        llm_panel = QFrame()
        llm_panel.setObjectName("PanelCard")
        llm_layout = QVBoxLayout(llm_panel)
        llm_layout.setContentsMargins(20, 18, 20, 18)
        llm_layout.setSpacing(10)

        self.llm_profiles: list[dict] = []
        self.llm_profile_combo = EditableModelComboBox()
        self.llm_profile_combo.setEditable(False)
        self.llm_profile_combo.currentIndexChanged.connect(self._select_llm_profile)

        delete_profile_btn = QPushButton("删除")
        delete_profile_btn.setObjectName("CompactDangerButton")
        delete_profile_btn.setFixedSize(82, 42)
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
        self.llm_timeout_input = NoWheelSpinBox()
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
        llm_root.addWidget(llm_panel)

        llm_root.addStretch(1)
        llm_scroll.setWidget(llm_content)
        self.stack.addWidget(llm_scroll)

        # page 2 - app settings (with subpanels)
        app_content = QWidget()
        app_content.setObjectName("SettingsContent")
        app_scroll = QScrollArea()
        app_scroll.setWidgetResizable(True)
        app_scroll.setFrameShape(QFrame.NoFrame)
        app_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        app_root = QVBoxLayout(app_content)
        app_root.setContentsMargins(26, 22, 26, 22)
        app_root.setSpacing(16)

        app_title = QLabel("⚙️ 应用设置")
        app_title.setObjectName("SectionTitle")
        app_root.addWidget(app_title)

        # -- general --
        self.confirm_close_check = QCheckBox("关闭时询问（最小化或退出）")
        gen_sub = QFrame()
        gen_sub.setObjectName("PanelCard")
        gen_sub_layout = QVBoxLayout(gen_sub)
        gen_sub_layout.setContentsMargins(20, 18, 20, 18)
        gen_sub_layout.setSpacing(10)
        gen_sub_title = QLabel("常规")
        gen_sub_title.setObjectName("SubSectionTitle")
        gen_sub_layout.addWidget(gen_sub_title)
        gen_sub_layout.addWidget(self._form_row("", self.confirm_close_check, compact=True))
        gen_sep = QFrame()
        gen_sep.setFrameShape(QFrame.HLine)
        gen_sep.setObjectName("SettingsSep")
        gen_sub_layout.addWidget(gen_sep)
        app_root.addWidget(gen_sub)

        # -- appearance --
        app_sub = QFrame()
        app_sub.setObjectName("PanelCard")
        app_sub_layout = QVBoxLayout(app_sub)
        app_sub_layout.setContentsMargins(20, 18, 20, 18)
        app_sub_layout.setSpacing(10)

        app_sub_title = QLabel("外观")
        app_sub_title.setObjectName("SubSectionTitle")
        app_sub_layout.addWidget(app_sub_title)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["跟随系统", "浅色模式", "深色模式"])
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        app_sub_layout.addWidget(self._form_row("主题", self.theme_combo))
        app_sep = QFrame()
        app_sep.setFrameShape(QFrame.HLine)
        app_sep.setObjectName("SettingsSep")
        app_sub_layout.addWidget(app_sep)

        app_root.addWidget(app_sub)

        # -- notification --
        notif_sub = QFrame()
        notif_sub.setObjectName("PanelCard")
        notif_layout = QVBoxLayout(notif_sub)
        notif_layout.setContentsMargins(20, 18, 20, 18)
        notif_layout.setSpacing(10)

        notif_sub_title = QLabel("通知")
        notif_sub_title.setObjectName("SubSectionTitle")
        notif_layout.addWidget(notif_sub_title)

        self.notify_enabled_check = QCheckBox("开启系统通知")
        notif_layout.addWidget(self._form_row("", self.notify_enabled_check, compact=True))

        self.notify_duration_spin = NoWheelSpinBox()
        self.notify_duration_spin.setRange(3, 60)
        self.notify_duration_spin.setSuffix(" 秒")
        notif_layout.addWidget(self._form_row("通知显示时长", self.notify_duration_spin))

        self.notify_startup_check = QCheckBox("启动时显示统计横幅")
        notif_layout.addWidget(self._form_row("", self.notify_startup_check, compact=True))
        notif_sep = QFrame()
        notif_sep.setFrameShape(QFrame.HLine)
        notif_sep.setObjectName("SettingsSep")
        notif_layout.addWidget(notif_sep)

        app_root.addWidget(notif_sub)

        # -- security --
        sec_sub = QFrame()
        sec_sub.setObjectName("PanelCard")
        sec_layout = QVBoxLayout(sec_sub)
        sec_layout.setContentsMargins(20, 18, 20, 18)
        sec_layout.setSpacing(10)

        sec_sub_title = QLabel("安全")
        sec_sub_title.setObjectName("SubSectionTitle")
        sec_layout.addWidget(sec_sub_title)

        self.desensitize_check = QCheckBox("日志数据脱敏（隐藏邮箱地址等敏感信息）")
        sec_layout.addWidget(self._form_row("", self.desensitize_check, compact=True))
        sec_sep = QFrame()
        sec_sep.setFrameShape(QFrame.HLine)
        sec_sep.setObjectName("SettingsSep")
        sec_layout.addWidget(sec_sep)

        app_root.addWidget(sec_sub)

        # save button
        actions = QHBoxLayout()
        actions.addStretch(1)
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save)
        actions.addWidget(save_btn)
        app_root.addLayout(actions)
        app_root.addStretch(1)

        app_scroll.setWidget(app_content)
        self.stack.addWidget(app_scroll)

        root.addWidget(self.stack, 1)

    def _switch_nav(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _on_theme_changed(self):
        theme_values = {0: "system", 1: "light", 2: "dark"}
        theme = theme_values[self.theme_combo.currentIndex()]
        if theme == "system":
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPalette
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            try:
                is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
            except AttributeError:
                palette = app.palette()
                c = palette.color(QPalette.Window)
                luminance = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
                is_dark = luminance < 128
        else:
            is_dark = theme == "dark"
        set_app_stylesheet(is_dark)

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

        app_cfg = config.get("app", {})
        self.confirm_close_check.setChecked(bool(app_cfg.get("confirm_close", True)))

        appearance_cfg = app_cfg.get("appearance", {})
        theme_map = {"system": 0, "light": 1, "dark": 2}
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(theme_map.get(appearance_cfg.get("theme", "system"), 0))
        self.theme_combo.blockSignals(False)

        notif_cfg = app_cfg.get("notification", {})
        self.notify_enabled_check.setChecked(bool(notif_cfg.get("enabled", True)))
        self.notify_duration_spin.setValue(int(notif_cfg.get("duration", 10)))
        self.notify_startup_check.setChecked(bool(notif_cfg.get("show_startup_banner", True)))

        sec_cfg = config.get("security", {})
        self.desensitize_check.setChecked(bool(sec_cfg.get("enable_desensitize", True)))

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

            theme_values = {0: "system", 1: "light", 2: "dark"}
            update_user_config("app", {
                "confirm_close": self.confirm_close_check.isChecked(),
                "close_action": "minimize",
                "appearance": {
                    "theme": theme_values[self.theme_combo.currentIndex()],
                },
                "notification": {
                    "enabled": self.notify_enabled_check.isChecked(),
                    "duration": self.notify_duration_spin.value(),
                    "show_startup_banner": self.notify_startup_check.isChecked(),
                },
            })

            update_user_config("security", {
                "enable_desensitize": self.desensitize_check.isChecked(),
            })

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
