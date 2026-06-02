from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
)


def parse_deadline(deadline: str | None):
    """
    返回 (QDate, hour, minute, has_time)
    """
    if not deadline:
        return QDate.currentDate(), 18, 0, False

    text = str(deadline).strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            has_time = fmt != "%Y-%m-%d"

            return (
                QDate(parsed.year, parsed.month, parsed.day),
                parsed.hour if has_time else 18,
                parsed.minute if has_time else 0,
                has_time,
            )
        except ValueError:
            continue

    return QDate.currentDate(), 18, 0, False


class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class CompactTimeSpin(QFrame):
    """
    紧凑型时间数字选择器：
    - 左侧显示数字；
    - 右侧独立 ▲ / ▼ 按钮；
    - 支持直接键盘输入；
    - 支持 wrapping 循环。
    """

    def __init__(
        self,
        minimum: int,
        maximum: int,
        value: int,
        zero_padding: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("CompactTimeSpin")

        self.zero_padding = zero_padding

        root = QHBoxLayout(self)

        # 关键修复：
        # 给外层边框预留 1px 内缩空间，
        # 避免右侧箭头区覆盖父容器底边框。
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.spin_box = NoWheelSpinBox()
        self.spin_box.setObjectName("CompactTimeValue")
        self.spin_box.setRange(minimum, maximum)
        self.spin_box.setValue(value)
        self.spin_box.setWrapping(True)
        self.spin_box.setButtonSymbols(QSpinBox.NoButtons)
        self.spin_box.setAlignment(Qt.AlignCenter)
        self.spin_box.setKeyboardTracking(False)
        self.spin_box.setFixedWidth(56)
        self.spin_box.setFixedHeight(44)

        if self.zero_padding:
            self.spin_box.textFromValue = self._text_from_value

        root.addWidget(self.spin_box)

        button_panel = QFrame()
        button_panel.setObjectName("CompactArrowPanel")
        button_panel.setFixedWidth(30)
        button_panel.setFixedHeight(44)

        button_layout = QVBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.up_button = QToolButton()
        self.up_button.setObjectName("CompactArrowButtonTop")
        self.up_button.setText("▲")
        self.up_button.setFixedSize(30, 22)
        self.up_button.clicked.connect(self.spin_box.stepUp)

        self.down_button = QToolButton()
        self.down_button.setObjectName("CompactArrowButtonBottom")
        self.down_button.setText("▼")
        self.down_button.setFixedSize(30, 22)
        self.down_button.clicked.connect(self.spin_box.stepDown)

        button_layout.addWidget(self.up_button)
        button_layout.addWidget(self.down_button)

        root.addWidget(button_panel)

        self.setFixedSize(88, 46)

    def _text_from_value(self, value: int) -> str:
        return f"{value:02d}"

    def value(self) -> int:
        return self.spin_box.value()

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.spin_box.setEnabled(enabled)
        self.up_button.setEnabled(enabled)
        self.down_button.setEnabled(enabled)

    def setFocusToEditor(self):
        self.spin_box.setFocus()
        self.spin_box.selectAll()


class DeadlineEditDialog(QDialog):
    """
    统一的截止时间编辑弹窗。

    - 点击日历选择日期；
    - 可选是否设置具体时间；
    - 小时 / 分钟分别调整；
    - 支持清除截止时间。
    """

    def __init__(self, current_deadline: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置截止时间")
        self.resize(520, 580)
        self.setModal(True)

        self.deadline_value: str | None = current_deadline
        (
            self._initial_date,
            self._initial_hour,
            self._initial_minute,
            self._initial_has_time,
        ) = parse_deadline(current_deadline)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QDialog {
                background: #f7f8fb;
            }

            QLabel#DialogTitle {
                font-size: 22px;
                font-weight: 900;
                color: #111827;
            }

            QLabel#DialogHint {
                font-size: 13px;
                color: #64748b;
            }

            QFrame#DeadlinePanel {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
            }

            QCalendarWidget {
                background: #ffffff;
                border: none;
                font-size: 14px;
            }

            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #f8fafc;
                border-bottom: 1px solid #e5e7eb;
            }

            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                color: #111827;
                font-size: 16px;
                font-weight: 900;
                background: transparent;
                border: none;
                padding: 2px 8px;
            }

            QCalendarWidget QToolButton#qt_calendar_monthbutton:hover,
            QCalendarWidget QToolButton#qt_calendar_yearbutton:hover {
                background: #eef2ff;
                border-radius: 8px;
            }

            QCalendarWidget QHeaderView {
                background: #ffffff;
                color: #64748b;
                font-size: 13px;
                font-weight: 800;
                border: none;
                padding: 0px;
            }

            QCalendarWidget QHeaderView::section {
                background: #ffffff;
                color: #64748b;
                font-size: 13px;
                font-weight: 800;
                border: none;
                padding: 4px 0px;
            }

            QCalendarWidget QAbstractItemView {
                background: #ffffff;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                color: #1f2937;
                font-size: 14px;
                outline: none;
                padding: 1px;
            }

            QCalendarWidget QAbstractItemView:disabled {
                color: #cbd5e1;
            }

            QCalendarWidget QAbstractItemView:enabled:hover {
                background: #dbeafe;
                color: #1d4ed8;
                border-radius: 20px;
            }

            QFrame#TimeSection {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }

            QCheckBox#HasTimeCheckBox {
                font-size: 14px;
                font-weight: 900;
                color: #334155;
                spacing: 8px;
            }

            QCheckBox#HasTimeCheckBox::indicator {
                width: 18px;
                height: 18px;
            }

            QLabel#TimeUnitLabel {
                color: #334155;
                font-size: 15px;
                font-weight: 900;
                padding-left: 4px;
                padding-right: 6px;
            }

            QLabel#TimeSeparator {
                color: #334155;
                font-size: 22px;
                font-weight: 900;
                padding-left: 3px;
                padding-right: 6px;
            }

            QLabel#TimeHint {
                font-size: 12px;
                color: #64748b;
            }

            QFrame#CompactTimeSpin {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
            }

            QFrame#CompactTimeSpin:focus-within {
                border: 1px solid #2563eb;
            }

            QSpinBox#CompactTimeValue {
                background: transparent;
                border: none;
                color: #111827;
                font-size: 16px;
                font-weight: 900;
                padding: 0;
            }

            QSpinBox#CompactTimeValue:disabled {
                color: #94a3b8;
            }

            QFrame#CompactArrowPanel {
                background: #ffffff;
                border-left: 1px solid #dbe3ee;
                border-top-right-radius: 11px;
                border-bottom-right-radius: 11px;
            }

            QToolButton#CompactArrowButtonTop,
            QToolButton#CompactArrowButtonBottom {
                background: transparent;
                border: none;
                color: #334155;
                font-size: 10px;
                font-weight: 900;
                padding: 0;
            }

            QToolButton#CompactArrowButtonTop {
                border-top-right-radius: 11px;
                border-bottom: 1px solid #e5e7eb;
            }

            QToolButton#CompactArrowButtonBottom {
                border-bottom-right-radius: 11px;
                border-bottom: 1px solid #cbd5e1;
            }

            QToolButton#CompactArrowButtonTop:hover,
            QToolButton#CompactArrowButtonBottom:hover {
                background: #eff6ff;
                color: #1d4ed8;
            }

            QToolButton#CompactArrowButtonTop:pressed,
            QToolButton#CompactArrowButtonBottom:pressed {
                background: #dbeafe;
            }

            QToolButton#CompactArrowButtonTop:disabled,
            QToolButton#CompactArrowButtonBottom:disabled {
                color: #cbd5e1;
                background: #f1f5f9;
            }

            QFrame#CompactTimeSpin:disabled {
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
            }

            QFrame#CompactArrowPanel:disabled {
                background: #f1f5f9;
                border-left: 1px solid #e2e8f0;
            }

            QPushButton#PrimaryAction {
                background: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 11px 20px;
                font-size: 14px;
                font-weight: 900;
            }

            QPushButton#PrimaryAction:hover {
                background: #1d4ed8;
            }

            QPushButton#SecondaryAction {
                background: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 11px 20px;
                font-size: 14px;
                font-weight: 800;
            }

            QPushButton#SecondaryAction:hover {
                background: #f8fafc;
                border: 1px solid #94a3b8;
            }

            QPushButton#DangerAction {
                background: #ffffff;
                color: #b91c1c;
                border: 1px solid #fecaca;
                border-radius: 12px;
                padding: 11px 20px;
                font-size: 14px;
                font-weight: 900;
            }

            QPushButton#DangerAction:hover {
                background: #fef2f2;
                border: 1px solid #fca5a5;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        title = QLabel("设置截止时间")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        hint = QLabel("选择日期；需要精确提醒时，再勾选具体时间。")
        hint.setObjectName("DialogHint")
        root.addWidget(hint)

        panel = QFrame()
        panel.setObjectName("DeadlinePanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(14)

        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(self._initial_date)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setMaximumDate(QDate(2099, 12, 31))
        self.calendar.setMinimumDate(QDate(2020, 1, 1))
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        panel_layout.addWidget(self.calendar)

        time_section = QFrame()
        time_section.setObjectName("TimeSection")
        time_section_layout = QVBoxLayout(time_section)
        time_section_layout.setContentsMargins(14, 12, 14, 12)
        time_section_layout.setSpacing(10)

        checkbox_row = QHBoxLayout()
        checkbox_row.setSpacing(12)

        self.has_time_checkbox = QCheckBox("设置具体时间")
        self.has_time_checkbox.setObjectName("HasTimeCheckBox")
        self.has_time_checkbox.setChecked(self._initial_has_time)
        self.has_time_checkbox.toggled.connect(self._sync_time_controls_state)
        checkbox_row.addWidget(self.has_time_checkbox)

        checkbox_row.addStretch(1)
        time_section_layout.addLayout(checkbox_row)

        selector_row = QHBoxLayout()
        selector_row.setSpacing(0)

        self.hour_selector = CompactTimeSpin(
            minimum=0,
            maximum=23,
            value=self._initial_hour,
            zero_padding=True,
        )
        selector_row.addWidget(self.hour_selector)

        hour_unit = QLabel("时")
        hour_unit.setObjectName("TimeUnitLabel")
        selector_row.addWidget(hour_unit)

        separator = QLabel(":")
        separator.setObjectName("TimeSeparator")
        selector_row.addWidget(separator)

        self.minute_selector = CompactTimeSpin(
            minimum=0,
            maximum=59,
            value=self._initial_minute,
            zero_padding=True,
        )
        selector_row.addWidget(self.minute_selector)

        minute_unit = QLabel("分")
        minute_unit.setObjectName("TimeUnitLabel")
        selector_row.addWidget(minute_unit)

        selector_row.addStretch(1)
        time_section_layout.addLayout(selector_row)

        self.time_hint = QLabel()
        self.time_hint.setObjectName("TimeHint")
        time_section_layout.addWidget(self.time_hint)

        panel_layout.addWidget(time_section)
        root.addWidget(panel, 1)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addStretch(1)

        clear_button = QPushButton("清除截止")
        clear_button.setObjectName("DangerAction")
        clear_button.clicked.connect(self._clear_deadline)
        action_row.addWidget(clear_button)

        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("SecondaryAction")
        cancel_button.clicked.connect(self.reject)
        action_row.addWidget(cancel_button)

        save_button = QPushButton("保存")
        save_button.setObjectName("PrimaryAction")
        save_button.clicked.connect(self._save_deadline)
        action_row.addWidget(save_button)

        root.addLayout(action_row)

        self._sync_time_controls_state(self._initial_has_time)

    def _sync_time_controls_state(self, checked: bool):
        self.hour_selector.setEnabled(checked)
        self.minute_selector.setEnabled(checked)

        if checked:
            self.time_hint.setText("已启用具体时间，可分别调整小时与分钟。")
        else:
            self.time_hint.setText("未启用具体时间，保存后只记录截止日期。")

    def _save_deadline(self):
        selected_date = self.calendar.selectedDate()
        date_text = selected_date.toString("yyyy-MM-dd")

        if self.has_time_checkbox.isChecked():
            hour = self.hour_selector.value()
            minute = self.minute_selector.value()
            self.deadline_value = f"{date_text} {hour:02d}:{minute:02d}"
        else:
            self.deadline_value = date_text

        self.accept()

    def _clear_deadline(self):
        self.deadline_value = None
        self.accept()