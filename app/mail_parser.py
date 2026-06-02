from email import message_from_bytes
from email.header import decode_header
from bs4 import BeautifulSoup


def decode_text(value):
    if not value:
        return ""

    parts = decode_header(value)
    result = ""

    for part, encoding in parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="ignore")
        else:
            result += part

    return result


# 提取邮件正文
def extract_body(msg):
    text_parts = []
    html_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            disposition = part.get_content_disposition()

            if disposition == "attachment":
                continue

            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            if not payload:
                continue

            charset = part.get_content_charset() or "utf-8"

            try:
                content = payload.decode(charset, errors="ignore")
            except Exception:
                content = payload.decode("utf-8", errors="ignore")

            if content_type == "text/plain":
                text_parts.append(content)

            elif content_type == "text/html":
                html_parts.append(content)

    else:
        payload = msg.get_payload(decode=True)

        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text_parts.append(payload.decode(charset, errors="ignore"))

    if text_parts:
        return "\n".join(text_parts).strip()

    if html_parts:
        soup = BeautifulSoup("\n".join(html_parts), "html.parser")
        return soup.get_text("\n").strip()

    return ""


# 解析
def parse_email(uid, raw_bytes, internal_date):
    msg = message_from_bytes(raw_bytes)

    return {
        "uid": str(uid),            # 邮件的唯一标识
        "from": decode_text(msg.get("From")),
        "to": decode_text(msg.get("To")),
        "cc": decode_text(msg.get("Cc")),
        "subject": decode_text(msg.get("Subject")),
        "date": str(internal_date),
        "message_id": msg.get("Message-ID", ""),
        "body": extract_body(msg)
    }