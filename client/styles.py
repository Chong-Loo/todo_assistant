APP_STYLESHEET = """
QMainWindow {
    background: #f6f8fb;
}

QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", Arial;
    font-size: 14px;
    color: #1f2937;
}

#AppRoot {
    background: #f6f8fb;
}

#Sidebar {
    background: #eef3f8;
    border-right: 1px solid #dbe3ec;
}

#SidebarTitle {
    font-size: 22px;
    font-weight: 800;
    color: #183b56;
    padding: 4px 2px 12px 2px;
}

#SidebarHint {
    color: #64748b;
    font-size: 12px;
    padding-bottom: 10px;
}

#SidebarSep {
    background: #dbe3ec;
    border: none;
    height: 1px;
    margin: 4px 0 10px 0;
}

QPushButton#NavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 12px 14px;
    text-align: left;
    font-weight: 700;
    color: #334155;
}

QPushButton#NavButton:hover {
    background: #e2e8f0;
}

QPushButton#NavButton:checked {
    background: #dbeafe;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
}

#HeaderPanel {
    background: white;
    border: 1px solid #e5eaf1;
    border-radius: 18px;
}

#HeaderWelcome {
    font-size: 18px;
    font-weight: 700;
    color: #000000;
}

#HeaderSubtitle {
    color: #64748b;
    font-size: 13px;
}

#SettingsNav {
    background: #eef3f8;
    border-right: 1px solid #dbe3ec;
    padding: 22px 0;
}

QPushButton#SettingsNavButton {
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 14px 18px;
    text-align: left;
    font-weight: 700;
    font-size: 14px;
    color: #334155;
}

QPushButton#SettingsNavButton:hover {
    background: #e2e8f0;
}

QPushButton#SettingsNavButton:checked {
    background: #dbeafe;
    border-left: 3px solid #2563eb;
    color: #1d4ed8;
}

#SettingsStack {
    background: transparent;
}

#SettingsContent {
    background: #ffffff;
}

QLabel#LlmWarning {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 10px 12px;
    font-weight: 900;
}

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

#SettingsGroupTitle {
    font-size: 16px;
    font-weight: 700;
    color: #1e293b;
    padding: 16px 0px 4px 0px;
}

#DbPathLabel {
    color: #64748b;
    font-size: 13px;
    font-family: "Consolas", "Courier New", monospace;
}

QPushButton#PrimaryButton {
    background: #2563eb;
    border: none;
    color: white;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 800;
}

QPushButton#PrimaryButton:hover {
    background: #1d4ed8;
}

QPushButton#PrimaryButton:disabled {
    background: #94a3b8;
}

QPushButton#SecondaryButton {
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 700;
}

QPushButton#SecondaryButton:hover {
    background: #f8fafc;
    border: 1px solid #94a3b8;
}

QFrame#MetricCard,
QFrame#TodoCard,
QFrame#PanelCard {
    background: white;
    border: 1px solid #e5eaf1;
    border-radius: 18px;
}

QFrame#TodoCard[highlight="true"] {
    border: 2px solid #2563eb;
    background: #ffffff;
}

#MetricLabel {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
}

#MetricValue {
    color: #0f172a;
    font-size: 30px;
    font-weight: 900;
}

#SectionTitle {
    font-size: 22px;
    font-weight: 900;
    color: #111827;
}

#SectionHint {
    color: #64748b;
    font-size: 13px;
}

#TodoTitle {
    font-size: 19px;
    font-weight: 900;
    color: #111827;
}

#TodoMeta {
    color: #64748b;
    font-size: 12px;
}

#TodoReason {
    color: #334155;
    line-height: 1.5;
}

#AttachmentRow {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

#AttachmentName {
    font-size: 13px;
    font-weight: 800;
    color: #111827;
}

#AttachmentMeta {
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

#StageRow {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

#StageTitle {
    font-size: 13px;
    font-weight: 800;
    color: #111827;
}

#StageDeadline {
    font-size: 12px;
    color: #64748b;
}

QLabel#StageTitle[done="true"] {
    color: #9ca3af;
    text-decoration: line-through;
}

QPushButton#StageCheck {
    border: 2px solid #d1d5db;
    border-radius: 4px;
    background-color: #ffffff;
    font-size: 16px;
    font-weight: 900;
    color: transparent;
    padding: 0px;
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
}

QPushButton#StageCheck:checked {
    background-color: #22c55e;
    border: 2px solid #16a34a;
    color: #ffffff;
}

QPushButton#StageCheck:hover {
    border-color: #94a3b8;
}

QPushButton#StageCheck:checked:hover {
    background-color: #16a34a;
    border-color: #16a34a;
}

QPushButton#DeleteStageButton {
    background: #ffffff;
    border: 1px solid #fecaca;
    color: #b91c1c;
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 800;
}

QPushButton#DeleteStageButton:hover {
    background: #fef2f2;
    border: 1px solid #fca5a5;
}

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

QPushButton#DeleteTodoButton {
    background: #ffffff;
    border: 1px solid #fecaca;
    color: #b91c1c;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 800;
}

QPushButton#DeleteTodoButton:hover {
    background: #fef2f2;
    border: 1px solid #fca5a5;
}

QToolButton#OperationToggle {
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

QToolButton#OperationToggle:hover {
    background: #f8fafc;
    border: 1px solid #94a3b8;
}

#OperationPanel {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
}

#OperationSection {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
}

#OperationTitle {
    color: #334155;
    font-size: 14px;
    font-weight: 900;
}

#OperationHint {
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

QLabel#BadgeUrgent {
    background: #fee2e2;
    color: #b91c1c;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeHigh {
    background: #ffedd5;
    color: #c2410c;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeNormal {
    background: #dbeafe;
    color: #1d4ed8;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeLow {
    background: #dcfce7;
    color: #15803d;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeOpen {
    background: #eef2ff;
    color: #4338ca;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeSnoozed {
    background: #fef3c7;
    color: #92400e;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeDone {
    background: #dcfce7;
    color: #166534;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeCancelled {
    background: #f3f4f6;
    color: #475569;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgePending {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #e2e8f0;
    border-radius: 11px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 800;
}

QLabel#BadgeOverdue {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 900;
}

QPushButton#BadgeUrgent {
    background: #fee2e2;
    color: #b91c1c;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeUrgent:hover {
    background: #fecaca;
}

QPushButton#BadgeHigh {
    background: #ffedd5;
    color: #c2410c;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeHigh:hover {
    background: #fed7aa;
}

QPushButton#BadgeNormal {
    background: #dbeafe;
    color: #1d4ed8;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeNormal:hover {
    background: #bfdbfe;
}

QPushButton#BadgeLow {
    background: #dcfce7;
    color: #15803d;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeLow:hover {
    background: #bbf7d0;
}

QComboBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 800;
    color: #334155;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #94a3b8;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    color: #1f2937;
    border: 1px solid #cbd5e1;
    selection-background-color: #dbeafe;
    selection-color: #1d4ed8;
    outline: 0;
}

QTableWidget {
    background: #ffffff;
    color: #1f2937;
    selection-background-color: #eef2ff;
    selection-color: #1d4ed8;
    alternate-background-color: #f8fafc;
    gridline-color: #e5e7eb;
}

QHeaderView::section {
    background: #f8fafc;
    color: #475569;
    font-weight: 800;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 8px 4px;
}

QLineEdit,
QTextEdit,
QSpinBox {
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 8px 10px;
}

QLineEdit:focus,
QTextEdit:focus,
QSpinBox:focus {
    border: 1px solid #2563eb;
}

QCheckBox {
    color: #334155;
    font-weight: 700;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea QWidget {
    background: white;
}

QStatusBar {
    background: white;
    border-top: 1px solid #e5eaf1;
    color: #475569;
}

QDialog {
    background: #f8fafc;
}

QTextBrowser {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px;
}

QProgressBar {
    background: #e2e8f0;
    border-radius: 14px;
    text-align: center;
    font-size: 12px;
    font-weight: 800;
    color: #1e293b;
    border: none;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6, stop:1 #2563eb);
    border-radius: 14px;
}

#RecentTodoCard {
    background: #ffffff;
    border: 1px solid #e5eaf1;
    border-radius: 14px;
}

#RecentTodoCard:hover {
    background: #fbfdff;
    border: 1px solid #bfdbfe;
}

#RecentTodoTitle {
    font-size: 14px;
    font-weight: 800;
    color: #111827;
}

#RecentTodoMeta {
    font-size: 12px;
    color: #64748b;
}

#RecentTodoDeadline {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 800;
}

QPushButton#ClearButton {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #475569;
    border-radius: 10px;
    padding: 0px 18px;
    min-height: 36px;
    max-height: 36px;
    font-weight: 700;
}

QPushButton#ClearButton:hover {
    background: #f8fafc;
    border: 1px solid #94a3b8;
}

#PopupTitle {
    font-size: 18px;
    font-weight: 900;
    color: #111827;
}

QPushButton#DangerButton {
    background: #dc2626;
    border: none;
    color: white;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 800;
}

QPushButton#DangerButton:hover {
    background: #b91c1c;
}
"""

DARK_APP_STYLESHEET = """
QMainWindow {
    background: #0f172a;
}

QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", Arial;
    font-size: 14px;
    color: #f1f5f9;
}

#AppRoot {
    background: #0f172a;
}

#Sidebar {
    background: #1e293b;
    border-right: 1px solid #334153;
}

#SidebarTitle {
    font-size: 22px;
    font-weight: 800;
    color: #f1f5f9;
    padding: 4px 2px 12px 2px;
}

#SidebarHint {
    color: #94a3b8;
    font-size: 12px;
    padding-bottom: 10px;
}

#SidebarSep {
    background: #334153;
    border: none;
    height: 1px;
    margin: 4px 0 10px 0;
}

QPushButton#NavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 12px 14px;
    text-align: left;
    font-weight: 700;
    color: #cbd5e1;
}

QPushButton#NavButton:hover {
    background: #334153;
}

QPushButton#NavButton:checked {
    background: #1e3a5f;
    border: 1px solid #3b82f6;
    color: #93c5fd;
}

#HeaderPanel {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 18px;
}

#HeaderWelcome {
    font-size: 18px;
    font-weight: 700;
    color: #f1f5f9;
}

#HeaderSubtitle {
    color: #94a3b8;
    font-size: 13px;
}

#SettingsNav {
    background: #1e293b;
    border-right: 1px solid #334153;
    padding: 22px 0;
}

QPushButton#SettingsNavButton {
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 14px 18px;
    text-align: left;
    font-weight: 700;
    font-size: 14px;
    color: #cbd5e1;
}

QPushButton#SettingsNavButton:hover {
    background: #334153;
}

QPushButton#SettingsNavButton:checked {
    background: #1e3a5f;
    border-left: 3px solid #3b82f6;
    color: #93c5fd;
}

#SettingsStack {
    background: transparent;
}

#SettingsContent {
    background: #1e293b;
}

QLabel#LlmWarning {
    background: #450a0a;
    color: #fca5a5;
    border: 1px solid #991b1b;
    border-radius: 10px;
    padding: 10px 12px;
    font-weight: 900;
}

QPushButton#CompactDangerButton {
    background: #1e293b;
    border: 1px solid #991b1b;
    color: #fca5a5;
    border-radius: 10px;
    font-weight: 900;
}

QPushButton#CompactDangerButton:hover {
    background: #450a0a;
    border: 1px solid #fca5a5;
}

#SettingsGroupTitle {
    font-size: 16px;
    font-weight: 700;
    color: #94a3b8;
    padding: 16px 0px 4px 0px;
}

#DbPathLabel {
    color: #94a3b8;
    font-size: 13px;
    font-family: "Consolas", "Courier New", monospace;
}

QPushButton#PrimaryButton {
    background: #3b82f6;
    border: none;
    color: white;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 800;
}

QPushButton#PrimaryButton:hover {
    background: #2563eb;
}

QPushButton#PrimaryButton:disabled {
    background: #475569;
}

QPushButton#SecondaryButton {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 700;
    color: #f1f5f9;
}

QPushButton#SecondaryButton:hover {
    background: #334153;
    border: 1px solid #64748b;
}

QFrame#MetricCard,
QFrame#TodoCard,
QFrame#PanelCard {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 18px;
}

QFrame#TodoCard[highlight="true"] {
    border: 2px solid #3b82f6;
    background: #1e293b;
}

#MetricLabel {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
}

#MetricValue {
    color: #f1f5f9;
    font-size: 30px;
    font-weight: 900;
}

#SectionTitle {
    font-size: 22px;
    font-weight: 900;
    color: #f1f5f9;
}

#SectionHint {
    color: #94a3b8;
    font-size: 13px;
}

#TodoTitle {
    font-size: 19px;
    font-weight: 900;
    color: #f1f5f9;
}

#TodoMeta {
    color: #94a3b8;
    font-size: 12px;
}

#TodoReason {
    color: #cbd5e1;
    line-height: 1.5;
}

#AttachmentRow {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 12px;
}

#AttachmentName {
    font-size: 13px;
    font-weight: 800;
    color: #f1f5f9;
}

#AttachmentMeta {
    font-size: 12px;
    color: #94a3b8;
}

QPushButton#DeleteAttachmentButton {
    background: #1e293b;
    border: 1px solid #991b1b;
    color: #fca5a5;
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 800;
}

QPushButton#DeleteAttachmentButton:hover {
    background: #450a0a;
    border: 1px solid #fca5a5;
}

#StageRow {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 12px;
}

#StageTitle {
    font-size: 13px;
    font-weight: 800;
    color: #f1f5f9;
}

#StageDeadline {
    font-size: 12px;
    color: #94a3b8;
}

QLabel#StageTitle[done="true"] {
    color: #64748b;
    text-decoration: line-through;
}

QPushButton#StageCheck {
    border: 2px solid #475569;
    border-radius: 4px;
    background-color: #1e293b;
    font-size: 16px;
    font-weight: 900;
    color: transparent;
    padding: 0px;
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
}

QPushButton#StageCheck:checked {
    background-color: #22c55e;
    border: 2px solid #16a34a;
    color: #ffffff;
}

QPushButton#StageCheck:hover {
    border-color: #64748b;
}

QPushButton#StageCheck:checked:hover {
    background-color: #16a34a;
    border-color: #16a34a;
}

QPushButton#DeleteStageButton {
    background: #1e293b;
    border: 1px solid #991b1b;
    color: #fca5a5;
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 800;
}

QPushButton#DeleteStageButton:hover {
    background: #450a0a;
    border: 1px solid #fca5a5;
}

QPushButton#DeadlineInlineButton {
    background: #0f172a;
    border: 1px solid #475569;
    color: #cbd5e1;
    border-radius: 12px;
    padding: 7px 12px;
    font-size: 13px;
    font-weight: 800;
    text-align: left;
}

QPushButton#DeadlineInlineButton:hover {
    background: #1e293b;
    border: 1px solid #3b82f6;
    color: #93c5fd;
}

QPushButton#DeleteTodoButton {
    background: #1e293b;
    border: 1px solid #991b1b;
    color: #fca5a5;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 800;
}

QPushButton#DeleteTodoButton:hover {
    background: #450a0a;
    border: 1px solid #fca5a5;
}

QToolButton#OperationToggle {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 14px;
    padding: 11px 16px;
    font-size: 15px;
    font-weight: 900;
    color: #cbd5e1;
    text-align: left;
    min-width: 92px;
}

QToolButton#OperationToggle:hover {
    background: #334153;
    border: 1px solid #64748b;
}

#OperationPanel {
    background: #0f172a;
    border: 1px solid #334153;
    border-radius: 18px;
}

#OperationSection {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 14px;
}

#OperationTitle {
    color: #cbd5e1;
    font-size: 14px;
    font-weight: 900;
}

#OperationHint {
    color: #94a3b8;
    font-size: 13px;
}

QPushButton#OperationButton {
    background: #1e293b;
    border: 1px solid #475569;
    color: #cbd5e1;
    border-radius: 11px;
    padding: 9px 14px;
    font-weight: 800;
}

QPushButton#OperationButton:hover {
    background: #334153;
    border: 1px solid #64748b;
}

QLabel#BadgeUrgent {
    background: #450a0a;
    color: #fca5a5;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeHigh {
    background: #431407;
    color: #fdba74;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeNormal {
    background: #1e3a5f;
    color: #93c5fd;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeLow {
    background: #14532d;
    color: #86efac;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeOpen {
    background: #1e1b4b;
    color: #a5b4fc;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeSnoozed {
    background: #451a03;
    color: #fde68a;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeDone {
    background: #14532d;
    color: #86efac;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgeCancelled {
    background: #334153;
    color: #cbd5e1;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
}

QLabel#BadgePending {
    background: #0f172a;
    color: #cbd5e1;
    border: 1px solid #475569;
    border-radius: 11px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 800;
}

QLabel#BadgeOverdue {
    background: #450a0a;
    color: #fca5a5;
    border: 1px solid #991b1b;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 900;
}

QPushButton#BadgeUrgent {
    background: #450a0a;
    color: #fca5a5;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeUrgent:hover {
    background: #7f1d1d;
}

QPushButton#BadgeHigh {
    background: #431407;
    color: #fdba74;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeHigh:hover {
    background: #7c2d12;
}

QPushButton#BadgeNormal {
    background: #1e3a5f;
    color: #93c5fd;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeNormal:hover {
    background: #1e40af;
}

QPushButton#BadgeLow {
    background: #14532d;
    color: #86efac;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 800;
    border: none;
}

QPushButton#BadgeLow:hover {
    background: #166534;
}

QComboBox {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 800;
    color: #cbd5e1;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #64748b;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: #1e293b;
    color: #f1f5f9;
    border: 1px solid #475569;
    selection-background-color: #334155;
    selection-color: #f1f5f9;
    outline: 0;
}

QTableWidget {
    background: #1e293b;
    color: #f1f5f9;
    selection-background-color: #334155;
    selection-color: #f1f5f9;
    alternate-background-color: #0f172a;
    gridline-color: #334153;
}

QHeaderView::section {
    background: #0f172a;
    color: #94a3b8;
    font-weight: 800;
    border: none;
    border-bottom: 1px solid #334153;
    padding: 8px 4px;
}

QLineEdit,
QTextEdit,
QSpinBox {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 8px 10px;
    color: #f1f5f9;
}

QLineEdit:focus,
QTextEdit:focus,
QSpinBox:focus {
    border: 1px solid #3b82f6;
}

QCheckBox {
    color: #cbd5e1;
    font-weight: 700;
}

QScrollArea {
    border: none;
    background: #1e293b;
}

QScrollArea QWidget {
    background: #1e293b;
}

QStatusBar {
    background: #1e293b;
    border-top: 1px solid #334153;
    color: #94a3b8;
}

QDialog {
    background: #1e293b;
}

QTextBrowser {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 12px;
    padding: 12px;
    color: #f1f5f9;
}

QProgressBar {
    background: #334153;
    border-radius: 14px;
    text-align: center;
    font-size: 12px;
    font-weight: 800;
    color: #f1f5f9;
    border: none;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #60a5fa, stop:1 #3b82f6);
    border-radius: 14px;
}

#RecentTodoCard {
    background: #1e293b;
    border: 1px solid #334153;
    border-radius: 14px;
}

#RecentTodoCard:hover {
    background: #334153;
    border: 1px solid #3b82f6;
}

#RecentTodoTitle {
    font-size: 14px;
    font-weight: 800;
    color: #f1f5f9;
}

#RecentTodoMeta {
    font-size: 12px;
    color: #94a3b8;
}

#RecentTodoDeadline {
    background: #0f172a;
    color: #cbd5e1;
    border: 1px solid #475569;
    border-radius: 12px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 800;
}

QPushButton#ClearButton {
    background: #1e293b;
    border: 1px solid #475569;
    color: #cbd5e1;
    border-radius: 10px;
    padding: 0px 18px;
    min-height: 36px;
    max-height: 36px;
    font-weight: 700;
}

QPushButton#ClearButton:hover {
    background: #334153;
    border: 1px solid #64748b;
}

#PopupTitle {
    font-size: 18px;
    font-weight: 900;
    color: #f1f5f9;
}

QPushButton#DangerButton {
    background: #b91c1c;
    border: none;
    color: white;
    border-radius: 14px;
    padding: 0px 22px;
    min-height: 52px;
    max-height: 52px;
    font-weight: 800;
}

QPushButton#DangerButton:hover {
    background: #991b1b;
}
"""


def set_app_stylesheet(is_dark: bool):
    from PySide6.QtWidgets import QApplication
    stylesheet = DARK_APP_STYLESHEET if is_dark else APP_STYLESHEET
    QApplication.instance().setStyleSheet(stylesheet)
