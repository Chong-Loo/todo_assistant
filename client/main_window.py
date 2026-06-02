from __future__ import annotations
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QButtonGroup,
    QStackedWidget,
    QMessageBox,
    QSpinBox,
    QSizePolicy,
)

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

        hint = QLabel("桌面客户端 MVP")
        hint.setObjectName("SidebarHint")
        sidebar_layout.addWidget(hint)

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

        header_text = QVBoxLayout()
        header_title = QLabel("智能待办助手")
        header_title.setObjectName("HeaderTitle")
        header_text.addWidget(header_title)

        header_subtitle = QLabel("读取 SQLite 待办、查看邮件正文，并支持手动触发邮件分析。")
        header_subtitle.setObjectName("HeaderSubtitle")
        header_text.addWidget(header_subtitle)
        header_layout.addLayout(header_text, 1)

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

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.header.setVisible(index == 0)

    def _refresh_all(self):
        self.dashboard_page.reload()
        self.email_page.reload()
        self.manual_page.reload()
        self.done_page.reload()
        self.settings_page.reload()
        self.statusBar().showMessage("数据已刷新", 3000)

    def _open_manual_dialog(self):
        dialog = ManualTodoDialog(self)
        if dialog.exec():
            self._refresh_all()
            self.statusBar().showMessage("人工待办已保存", 4000)

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

        self.worker_thread = DailyJobThread(lookback_days=lookback_days, parent=self)
        self.worker_thread.started_message.connect(self.statusBar().showMessage)
        self.worker_thread.success.connect(self._on_job_success)
        self.worker_thread.failed.connect(self._on_job_failed)
        self.worker_thread.finished.connect(lambda: self.analyze_button.setEnabled(True))
        self.worker_thread.start()

    def _on_job_success(self, message: str):
        self._refresh_all()
        self.statusBar().showMessage(message, 6000)
        QMessageBox.information(self, "分析完成", message)

    def _on_job_failed(self, message: str):
        self.statusBar().showMessage("邮件分析失败", 6000)
        QMessageBox.critical(self, "邮件分析失败", message)

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
