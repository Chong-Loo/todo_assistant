from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal


class DailyJobThread(QThread):
    """
    后台执行邮件分析，避免桌面界面卡死。
    """
    started_message = Signal(str)
    progress = Signal(int, int)
    cancelled = Signal(str)
    success = Signal(str)
    failed = Signal(str)

    def __init__(self, lookback_days: int | None = None, parent=None):
        super().__init__(parent)
        self.lookback_days = lookback_days
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        try:
            self.started_message.emit("正在读取邮件并调用大模型分析...")
            from main import run_daily_job

            def _on_progress(current, total):
                self.progress.emit(current, total)

            def _stop_check():
                return self._stop_requested

            run_daily_job(
                lookback_days=self.lookback_days,
                on_progress=_on_progress,
                stop_check=_stop_check,
            )

            if self._stop_requested:
                self.cancelled.emit("分析已取消，已保存部分结果。")
            else:
                self.success.emit("邮件分析完成，待办数据已刷新。")
        except Exception as exc:
            message = f"{exc}\n\n{traceback.format_exc()}"
            self.failed.emit(message)
