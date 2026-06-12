from __future__ import annotations
from PySide6.QtCore import QTime, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QWidget,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

from app.email_tracker import clear_tracking
from app.settings import load_config, update_user_config
from app.todo_manager import load_normalized_todos
from client.pages.dashboard_page import DashboardPage
from client.pages.settings_page import SettingsPage
from client.pages.todo_page import TodoPage
from client.widgets.manual_todo_dialog import ManualTodoDialog
from client.widgets.painted_combo_box import PaintedComboBox
from client.workers.daily_job_worker import DailyJobThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能待办助手")
        self.resize(1360, 860)

        self.worker_thread: DailyJobThread | None = None

        self._build_ui()
        self._setup_tray()
        self._update_welcome()
        self._refresh_all()

    def _build_ui(self):
        app_root = QWidget()
        app_root.setObjectName("AppRoot")
        self.setCentralWidget(app_root)

        root = QHBoxLayout(app_root)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 22, 18, 22)
        sidebar_layout.setSpacing(10)

        title = QLabel("📬 智能待办助手")
        title.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("SidebarSep")
        sidebar_layout.addWidget(sep)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("主页", 0),
            ("邮件待办", 1),
            ("人工待办", 2),
            ("已完成", 3),
            ("设置", 4),
        ]

        for index, (label, page_index) in enumerate(nav_items):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=page_index: self._switch_page(i))
            sidebar_layout.addWidget(button)
            self.nav_group.addButton(button, page_index)
            if index == 0:
                button.setChecked(True)

        sidebar_layout.addStretch(1)

        add_button = QPushButton("＋ 人工添加")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self._open_manual_dialog)
        sidebar_layout.addWidget(add_button)

        root.addWidget(sidebar)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(26, 22, 26, 22)
        body_layout.setSpacing(18)

        self.header = QFrame()
        self.header.setObjectName("HeaderPanel")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(22, 18, 22, 18)
        header_layout.setSpacing(16)

        self.header_welcome = QLabel()
        self.header_welcome.setObjectName("HeaderWelcome")
        header_layout.addWidget(self.header_welcome, 1)

        self.lookback_combo = PaintedComboBox()
        self.lookback_combo.addItem("最新邮件（增量）", 0)
        self.lookback_combo.addItem("按天拉取", -1)
        self.lookback_combo.currentIndexChanged.connect(self._on_lookback_mode_changed)
        header_layout.addWidget(self.lookback_combo)

        self.lookback_spinbox = QSpinBox()
        self.lookback_spinbox.setRange(1, 30)
        self.lookback_spinbox.setValue(1)
        self.lookback_spinbox.setSuffix(" 天")
        self.lookback_spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self.lookback_spinbox.setMinimumHeight(48)
        self.lookback_spinbox.setMaximumHeight(48)
        self.lookback_spinbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lookback_spinbox.setFixedWidth(100)
        self.lookback_spinbox.hide()
        header_layout.addWidget(self.lookback_spinbox)

        self.analyze_button = QPushButton("立即分析邮件")
        self.analyze_button.setObjectName("PrimaryButton")
        self.analyze_button.clicked.connect(self._run_daily_job)
        header_layout.addWidget(self.analyze_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.hide()
        header_layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("取消分析")
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.clicked.connect(self._cancel_analysis)
        self.cancel_button.hide()
        header_layout.addWidget(self.cancel_button)

        reset_tracking_btn = QPushButton("清空拉取记录")
        reset_tracking_btn.setObjectName("SecondaryButton")
        reset_tracking_btn.clicked.connect(self._reset_email_tracking)
        header_layout.addWidget(reset_tracking_btn)

        refresh_button = QPushButton("刷新数据")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self._refresh_all)
        header_layout.addWidget(refresh_button)

        body_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.dashboard_page.todo_selected.connect(self._jump_to_todo)

        self.email_page = TodoPage("邮件生成待办", "email")
        self.manual_page = TodoPage("人工添加待办", "manual")
        self.done_page = TodoPage("已完成待办", "done")
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.email_page)
        self.stack.addWidget(self.manual_page)
        self.stack.addWidget(self.done_page)
        self.stack.addWidget(self.settings_page)

        body_layout.addWidget(self.stack, 1)

        root.addWidget(body, 1)

        self.statusBar().showMessage("就绪")

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon())
        self.tray.setToolTip("智能待办助手")

        tray_menu = QMenu(self)
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self._tray_show)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self._tray_quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_show(self):
        self.show()
        self.activateWindow()

    def _tray_quit(self):
        self.tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self._tray_show()

    def _compute_welcome_text(self):
        from app.todo_status import is_todo_overdue
        todos = load_normalized_todos(cleanup=False)
        active = [t for t in todos if t.get("status", "open") in {"open", "snoozed"}]

        overdue = [t for t in active if is_todo_overdue(t)]
        urgent = [t for t in active if t.get("priority") == "urgent" and not is_todo_overdue(t)]
        high = [t for t in active if t.get("priority") == "high" and not is_todo_overdue(t)]

        hour = QTime.currentTime().hour()
        if 6 <= hour < 11:
            time_greeting = "☀️ 早上好！"
        elif 11 <= hour < 14:
            time_greeting = "🌞 午安！"
        elif 14 <= hour < 18:
            time_greeting = "☀️ 下午好！"
        elif 18 <= hour < 23:
            time_greeting = "🌇 傍晚好！"
        else:
            time_greeting = "🌙 夜深了..."

        count = len(active)

        if overdue:
            text = f"{time_greeting}您有 {len(overdue)} 条已逾期待办"
        elif urgent:
            text = f"{time_greeting}您有 {len(urgent)} 条紧急待办"
        elif high:
            text = f"{time_greeting}您有 {len(high)} 条高优先级待办"
        elif count > 0:
            text = f"{time_greeting}{count} 件事待处理"
        else:
            text = f"{time_greeting}今天状态不错！"

        return text

    def _update_welcome(self):
        text = self._compute_welcome_text()
        self.header_welcome.setText(text)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_welcome()

    def closeEvent(self, event):
        config = load_config()
        app_conf = config.get("app", {})
        confirm_close = app_conf.get("confirm_close", True)
        close_action = app_conf.get("close_action", "minimize")

        if not confirm_close:
            if close_action == "minimize":
                event.ignore()
                self.hide()
                self.tray.showMessage("智能待办助手", "已最小化到后台运行",
                                      QSystemTrayIcon.Information, 2000)
            else:
                event.accept()
                self.tray.hide()
                from PySide6.QtWidgets import QApplication
                QApplication.instance().quit()
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("确认退出")
        msg.setText("如何处理智能待办助手？")
        msg.setIcon(QMessageBox.Question)

        dont_ask = QCheckBox("不再询问")
        msg.setCheckBox(dont_ask)

        minimize_btn = msg.addButton("最小化到后台", QMessageBox.AcceptRole)
        quit_btn = msg.addButton("退出程序", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("取消", QMessageBox.RejectRole)
        msg.setDefaultButton(minimize_btn)

        msg.exec()

        clicked = msg.clickedButton()
        dont_ask_flag = dont_ask.isChecked()

        if clicked == cancel_btn:
            event.ignore()
            return

        if clicked == minimize_btn:
            if dont_ask_flag:
                update_user_config("app", {"confirm_close": False, "close_action": "minimize"})
            event.ignore()
            self.hide()
            self.tray.showMessage("智能待办助手", "已最小化到后台运行",
                                  QSystemTrayIcon.Information, 2000)
        elif clicked == quit_btn:
            if dont_ask_flag:
                update_user_config("app", {"confirm_close": False, "close_action": "quit"})
            event.accept()
            self.tray.hide()
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.header.setVisible(index == 0)
        if index == 0:
            self._update_welcome()

    def _refresh_all(self):
        self.dashboard_page.reload()
        self.email_page.reload()
        self.manual_page.reload()
        self.done_page.reload()
        self.settings_page.reload()
        self._update_welcome()
        self.statusBar().showMessage("数据已刷新", 3000)

    def _open_manual_dialog(self):
        dialog = ManualTodoDialog(parent=self)
        if dialog.exec():
            self._refresh_all()
            self.statusBar().showMessage("人工待办已保存", 4000)

    def _reset_email_tracking(self):
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
            clear_tracking()
            QMessageBox.information(self, "操作完成", "邮件拉取记录已清空，下次分析将重新拉取所有邮件。")
        except Exception as exc:
            QMessageBox.critical(self, "操作失败", str(exc))

    def _on_lookback_mode_changed(self):
        mode = self.lookback_combo.currentData()
        self.lookback_spinbox.setVisible(mode == -1)

    def _run_daily_job(self):
        if self.worker_thread and self.worker_thread.isRunning():
            return

        mode = self.lookback_combo.currentData()
        lookback_days = self.lookback_spinbox.value() if mode == -1 else 0
        self.analyze_button.setEnabled(False)
        self.statusBar().showMessage("正在执行邮件分析...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.cancel_button.show()

        self.worker_thread = DailyJobThread(lookback_days=lookback_days, parent=self)
        self.worker_thread.started_message.connect(self.statusBar().showMessage)
        self.worker_thread.progress.connect(self._on_analysis_progress)
        self.worker_thread.success.connect(self._on_job_success)
        self.worker_thread.cancelled.connect(self._on_job_cancelled)
        self.worker_thread.failed.connect(self._on_job_failed)
        self.worker_thread.finished.connect(self._on_analysis_finished)
        self.worker_thread.start()

    def _cancel_analysis(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.request_stop()
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("正在取消...")
            self.statusBar().showMessage("正在取消分析，请等待当前邮件分析完成...")

    def _on_analysis_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"正在分析 %v/%m 封邮件")
        self.statusBar().showMessage(f"正在分析第 {current}/{total} 封邮件...")

    def _on_job_success(self, message: str):
        self._refresh_all()
        self.statusBar().showMessage(message, 6000)
        QMessageBox.information(self, "分析完成", message)

    def _on_job_cancelled(self, message: str):
        self._refresh_all()
        self.statusBar().showMessage(message, 6000)
        QMessageBox.information(self, "分析已取消", message)

    def _on_job_failed(self, message: str):
        self.statusBar().showMessage("邮件分析失败", 6000)
        QMessageBox.critical(self, "邮件分析失败", message)

    def _on_analysis_finished(self):
        self.analyze_button.setEnabled(True)
        self.progress_bar.hide()
        self.cancel_button.hide()
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("取消分析")

    def _jump_to_todo(self, todo_id: str):
        todos = load_normalized_todos(cleanup=True)
        target = next(
            (todo for todo in todos if str(todo.get("id", "")) == str(todo_id)),
            None
        )

        if not target:
            QMessageBox.information(self, "提示", "未找到对应待办。")
            return

        if target.get("status") == "done":
            page_index = 3
            page = self.done_page
        elif target.get("is_manual"):
            page_index = 2
            page = self.manual_page
        else:
            page_index = 1
            page = self.email_page

        self.stack.setCurrentIndex(page_index)

        nav_button = self.nav_group.button(page_index)
        if nav_button:
            nav_button.setChecked(True)

        def focus_after_page_switched():
            focused = page.focus_todo(str(todo_id))
            if focused:
                self.statusBar().showMessage("已跳转到对应待办。", 4000)
            else:
                self.statusBar().showMessage("已切换页面，但未能定位到待办卡片。", 4000)

        QTimer.singleShot(80, focus_after_page_switched)
