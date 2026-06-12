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

QLabel#BadgeOverdue {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 900;
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
"""
