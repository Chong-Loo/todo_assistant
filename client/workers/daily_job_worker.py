from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal


class DailyJobThread(QThread):
    """
    后台执行邮件分析，避免桌面界面卡死。
    """
    started_message = Signal(str)
    success = Signal(str)
    failed = Signal(str)

    def __init__(self, lookback_days: int | None = None, parent=None):
        super().__init__(parent)
        self.lookback_days = lookback_days

    def run(self):
        try:
            self.started_message.emit("正在读取邮件并调用大模型分析...")
            from main import run_daily_job

            run_daily_job(lookback_days=self.lookback_days)
            self.success.emit("邮件分析完成，待办数据已刷新。")
        except Exception as exc:
            message = f"{exc}\n\n{traceback.format_exc()}"
            self.failed.emit(message)
