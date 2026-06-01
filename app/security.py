import re


def desensitize_text(text: str) -> str:
    text = re.sub(r"\b1[3-9]\d{9}\b", "[手机号]", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[邮箱]", text)
    text = re.sub(r"\b\d{15,18}\b", "[长数字编号]", text)
    return text