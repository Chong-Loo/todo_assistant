from __future__ import annotations

import re
from html import escape, unescape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QPushButton,
    QToolButton,
    QFrame,
    QScrollArea,
    QWidget,
)


EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?![\w.-])"
)


def normalize_mail_body(body: str | None) -> str:
    """
    规范化邮件正文：
    1. 统一换行符；
    2. 去除每行右侧无意义空白；
    3. 合并过量空行；
    4. 去掉正文首尾空白。
    """
    if not body:
        return "该待办未保存来源邮件正文。"

    text = unescape(str(body))
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [line.rstrip() for line in text.split("\n")]

    normalized_lines: list[str] = []
    blank_count = 0

    for line in lines:
        if line.strip():
            blank_count = 0
            normalized_lines.append(line.strip())
        else:
            blank_count += 1
            if blank_count <= 1:
                normalized_lines.append("")

    normalized = "\n".join(normalized_lines).strip()
    return normalized or "该待办未保存来源邮件正文。"


def render_text_with_email_links(text: str) -> str:
    """
    将普通文本转为安全 HTML，并将邮箱地址渲染为 mailto 链接。
    """
    safe_text = escape(text)

    def replace_email(match: re.Match[str]) -> str:
        email = match.group(1)
        return (
            f"<a href='mailto:{email}' "
            "style='color:#0369a1; text-decoration:underline;'>"
            f"{email}</a>"
        )

    return EMAIL_PATTERN.sub(replace_email, safe_text)


def build_mail_body_html(body: str | None) -> str:
    """
    将正文构造成更接近正式邮件阅读体验的 HTML。
    - 空行作为段落分隔；
    - 段落内部换行保留；
    - 邮箱地址转为链接。
    """
    normalized = normalize_mail_body(body)
    paragraphs = re.split(r"\n\s*\n", normalized)

    html_parts: list[str] = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        rendered_lines = [
            render_text_with_email_links(line)
            for line in paragraph.split("\n")
        ]
        paragraph_html = "<br>".join(rendered_lines)

        html_parts.append(
            "<p style='"
            "margin: 0 0 14px 0;"
            "padding: 0;"
            "line-height: 1.85;"
            "font-size: 15px;"
            "color: #111827;"
            "'>"
            f"{paragraph_html}"
            "</p>"
        )

    if not html_parts:
        html_parts.append(
            "<p style='"
            "margin: 0;"
            "line-height: 1.85;"
            "font-size: 15px;"
            "color: #111827;"
            "'>"
            "该待办未保存来源邮件正文。"
            "</p>"
        )

    return (
        "<div style='"
        "font-family: Microsoft YaHei, PingFang SC, Arial, sans-serif;"
        "color: #111827;"
        "'>"
        + "".join(html_parts)
        + "</div>"
    )


class MailDetailDialog(QDialog):
    """
    来源邮件正文弹窗。

    优化目标：
    1. 顶部保留主题 / 发件人 / 时间；
    2. 收件人 / 抄送人默认折叠；
    3. 正文改为更接近正式邮件阅读的排版；
    4. 自动压缩无意义留白；
    5. 短邮件正文区域不再出现大面积空白；
    6. 长邮件仍可在正文框内滚动查看。
    """

    def __init__(self, todo: dict, parent=None):
        super().__init__(parent)
        self.todo = todo
        self.setWindowTitle("查看来源邮件正文")
        self.resize(1080, 780)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QDialog {
                background: #f7f8fb;
            }

            QLabel#DialogTitle {
                font-size: 24px;
                font-weight: 900;
                color: #111827;
            }

            QLabel#MailInfoLine {
                font-size: 16px;
                color: #1f2937;
                line-height: 1.8;
            }

            QToolButton#RecipientToggle {
                background: #ffffff;
                border: 1px solid #d7dee8;
                border-radius: 12px;
                color: #334155;
                padding: 11px 16px;
                font-size: 15px;
                font-weight: 800;
                text-align: left;
            }

            QToolButton#RecipientToggle:hover {
                background: #f8fafc;
                border: 1px solid #bfdbfe;
            }

            QFrame#RecipientPanel {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }

            QScrollArea#RecipientScroll {
                background: transparent;
                border: none;
            }

            QLabel#RecipientText {
                color: #1f2937;
                font-size: 14px;
                line-height: 1.75;
            }

            QLabel#BodyTitle {
                font-size: 18px;
                font-weight: 900;
                color: #111827;
            }

            QTextBrowser#BodyBox {
                background: #ffffff;
                color: #111827;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 18px 20px;
                font-size: 15px;
            }

            QPushButton#SecondaryButton {
                background: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 11px 22px;
                font-size: 14px;
                font-weight: 900;
            }

            QPushButton#SecondaryButton:hover {
                background: #f8fafc;
                border: 1px solid #94a3b8;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        source_mail = self.todo.get("source_mail") or {}

        subject = (
            source_mail.get("subject")
            or self.todo.get("source_subject")
            or "未提供主题"
        )
        sender = (
            source_mail.get("from")
            or self.todo.get("source_from")
            or "未提供发件人"
        )
        date_text = (
            source_mail.get("date")
            or self.todo.get("source_date")
            or "未提供时间"
        )
        recipients_to = source_mail.get("to") or "无"
        recipients_cc = source_mail.get("cc") or "无"
        body_text = source_mail.get("body")

        title = QLabel("查看来源邮件正文")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        subject_label = QLabel(
            f"<b>主题：</b> {escape(str(subject))}"
        )
        subject_label.setTextFormat(Qt.RichText)
        subject_label.setWordWrap(True)
        subject_label.setObjectName("MailInfoLine")
        root.addWidget(subject_label)

        sender_label = QLabel(
            f"<b>发件人：</b> {render_text_with_email_links(str(sender))}"
        )
        sender_label.setTextFormat(Qt.RichText)
        sender_label.setWordWrap(True)
        sender_label.setOpenExternalLinks(True)
        sender_label.setObjectName("MailInfoLine")
        root.addWidget(sender_label)

        date_label = QLabel(
            f"<b>时间：</b> {escape(str(date_text))}"
        )
        date_label.setTextFormat(Qt.RichText)
        date_label.setWordWrap(True)
        date_label.setObjectName("MailInfoLine")
        root.addWidget(date_label)

        self.recipient_toggle = QToolButton()
        self.recipient_toggle.setObjectName("RecipientToggle")
        self.recipient_toggle.setText("收件人 / 抄送人")
        self.recipient_toggle.setCheckable(True)
        self.recipient_toggle.setChecked(False)
        self.recipient_toggle.setArrowType(Qt.RightArrow)
        self.recipient_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.recipient_toggle.clicked.connect(self._toggle_recipients)
        root.addWidget(self.recipient_toggle)

        self.recipient_panel = QFrame()
        self.recipient_panel.setObjectName("RecipientPanel")

        recipient_panel_layout = QVBoxLayout(self.recipient_panel)
        recipient_panel_layout.setContentsMargins(16, 14, 16, 14)
        recipient_panel_layout.setSpacing(8)

        recipient_scroll = QScrollArea()
        recipient_scroll.setObjectName("RecipientScroll")
        recipient_scroll.setWidgetResizable(True)
        recipient_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        recipient_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        recipient_scroll.setMinimumHeight(96)
        recipient_scroll.setMaximumHeight(220)

        recipient_content = QWidget()
        recipient_content_layout = QVBoxLayout(recipient_content)
        recipient_content_layout.setContentsMargins(0, 0, 0, 0)
        recipient_content_layout.setSpacing(8)

        to_label = QLabel(
            f"<b>收件人：</b> {render_text_with_email_links(str(recipients_to))}"
        )
        to_label.setTextFormat(Qt.RichText)
        to_label.setWordWrap(True)
        to_label.setOpenExternalLinks(True)
        to_label.setObjectName("RecipientText")
        recipient_content_layout.addWidget(to_label)

        cc_label = QLabel(
            f"<b>抄送人：</b> {render_text_with_email_links(str(recipients_cc))}"
        )
        cc_label.setTextFormat(Qt.RichText)
        cc_label.setWordWrap(True)
        cc_label.setOpenExternalLinks(True)
        cc_label.setObjectName("RecipientText")
        recipient_content_layout.addWidget(cc_label)

        recipient_scroll.setWidget(recipient_content)
        recipient_panel_layout.addWidget(recipient_scroll)

        self.recipient_panel.setVisible(False)
        root.addWidget(self.recipient_panel)

        body_title = QLabel("邮件正文")
        body_title.setObjectName("BodyTitle")
        root.addWidget(body_title)

        self.body_box = QTextBrowser()
        self.body_box.setObjectName("BodyBox")
        self.body_box.setOpenExternalLinks(True)
        self.body_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body_box.setHtml(build_mail_body_html(body_text))
        root.addWidget(self.body_box, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)

        close_button = QPushButton("关闭")
        close_button.setObjectName("SecondaryButton")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)

        root.addLayout(footer)

    def _toggle_recipients(self, checked: bool):
        self.recipient_panel.setVisible(checked)
        self.recipient_toggle.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )