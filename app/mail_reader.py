from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from pathlib import Path
import time

from imapclient import IMAPClient

from app.mail_parser import parse_email
from app.mail_classifier import classify_delivery_type
from app.settings import get_mail_password, load_config


LOCAL_TIMEZONE = "Asia/Shanghai"

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def get_body_bytes(data: dict) -> bytes:
    """
    兼容不同 IMAP 服务器返回的 BODY.PEEK key。

    例如：
    b'BODY[]<0>'
    b'BODY[]<0.80000>'
    b'BODY[TEXT]<0>'
    """
    for key, value in data.items():
        if isinstance(key, bytes) and key.upper().startswith(b"BODY"):
            return value

    return b""


def get_header_bytes(data: dict) -> bytes:
    """
    不同 IMAP 服务器返回的 HEADER key 可能略有差异，
    所以这里做兼容查找。
    """
    for key, value in data.items():
        if isinstance(key, bytes) and key.upper().startswith(b"BODY[HEADER"):
            return value

    return b""


def parse_header_date(header_bytes: bytes, tz: ZoneInfo):
    """
    从邮件 Header 的 Date 字段解析真实发送时间。
    解析失败则返回 None。
    """
    if not header_bytes:
        return None

    try:
        msg = message_from_bytes(header_bytes)
        raw_date = msg.get("Date")

        if not raw_date:
            return None

        mail_date = parsedate_to_datetime(raw_date)

        if mail_date.tzinfo is None:
            mail_date = mail_date.replace(tzinfo=tz)
        else:
            mail_date = mail_date.astimezone(tz)

        return mail_date

    except Exception:
        return None


def normalize_internal_date(internal_date, tz: ZoneInfo):
    if internal_date.tzinfo is None:
        return internal_date.replace(tzinfo=tz)

    return internal_date.astimezone(tz)


def get_task_config(config):
    task_cfg = config.get("task", {})

    lookback_days = int(task_cfg.get("lookback_days", 1))

    # 每封邮件最多下载多少字节。
    # 80KB 通常足够提取正文和待办，也能避免把大附件一起拉下来。
    max_email_bytes = int(task_cfg.get("max_email_bytes", 80_000))

    return lookback_days, max_email_bytes


def fetch_today_emails(lookback_days=None, max_email_bytes=None):
    """
    业务口径：
    默认读取最近 lookback_days 天，从 N 天前 00:00 到当前时刻之间的邮件。

    性能优化：
    1. 先 IMAP SEARCH 粗筛。
    2. 只拉 Header + INTERNALDATE + RFC822.SIZE。
    3. 用 Header Date 精确过滤。
    4. 对命中的 UID 只拉前 max_email_bytes 字节。
    5. 不下载完整 RFC822，尽量避免下载附件。
    """

    config = load_config()
    mail_cfg = config["mail"]

    default_lookback_days, default_max_email_bytes = get_task_config(config)

    if lookback_days is None:
        lookback_days = default_lookback_days
    else:
        lookback_days = int(lookback_days)

    if max_email_bytes is None:
        max_email_bytes = default_max_email_bytes
    else:
        max_email_bytes = int(max_email_bytes)

    username = mail_cfg["username"]
    password = get_mail_password(username)

    if not password:
        raise RuntimeError("没有读取到邮箱密码")

    tz = ZoneInfo(LOCAL_TIMEZONE)

    now = datetime.now(tz)
    start_time = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    ) - timedelta(days=lookback_days)

    since_date = start_time.strftime("%d-%b-%Y")

    print(f"精确过滤时间: {start_time} ~ {now}")
    print(f"IMAP粗筛起始日期: {since_date}")
    print(f"邮件下载上限: 每封最多 {max_email_bytes / 1024:.0f}KB")

    emails = []

    with IMAPClient(
        mail_cfg["host"],
        port=mail_cfg["port"],
        ssl=mail_cfg.get("use_ssl", True)
    ) as client:

        client.login(username, password)
        client.select_folder(mail_cfg.get("folder", "INBOX"))

        t0 = time.time()

        messages = client.search(["SINCE", since_date])

        print(f"IMAP粗筛邮件数量: {len(messages)}")
        print(f"SEARCH耗时: {time.time() - t0:.2f}s")

        if not messages:
            return []

        # 第一阶段：只拉 Header，不拉正文、不拉附件
        t1 = time.time()

        header_response = client.fetch(
            messages,
            [
                "INTERNALDATE",
                "RFC822.SIZE",
                "BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO CC DATE MESSAGE-ID)]"
            ]
        )

        print(f"HEADER FETCH耗时: {time.time() - t1:.2f}s")

        valid_uids = []
        uid_date_map = {}
        uid_size_map = {}

        for uid, data in header_response.items():
            header_bytes = get_header_bytes(data)

            # 优先用邮件 Header Date
            mail_date = parse_header_date(header_bytes, tz)

            # Header Date 解析失败时，再用 INTERNALDATE 兜底
            if mail_date is None:
                internal_date = data.get(b"INTERNALDATE")

                if internal_date:
                    mail_date = normalize_internal_date(internal_date, tz)

            if mail_date is None:
                continue

            if start_time <= mail_date <= now:
                valid_uids.append(uid)
                uid_date_map[uid] = mail_date
                uid_size_map[uid] = data.get(b"RFC822.SIZE", 0)

        print(f"精确时间过滤后 UID 数量: {len(valid_uids)}")

        if not valid_uids:
            return []

        for uid in valid_uids:
            size = uid_size_map.get(uid, 0)

            if size:
                print(f"待拉取邮件 UID={uid}, 原始大小={size / 1024:.1f}KB")

        # 第二阶段：只对真正需要的邮件拉取前 max_email_bytes 字节
        # 注意：这里不是下载完整 RFC822，而是下载邮件开头的一段。
        # 对大多数邮件来说，Header + 正文都在前面，附件通常在后面。
        t2 = time.time()

        fetch_body_key = f"BODY.PEEK[]<0.{max_email_bytes}>"

        body_response = client.fetch(
            valid_uids,
            [fetch_body_key]
        )

        print(f"部分邮件内容 FETCH耗时: {time.time() - t2:.2f}s")

        for uid, data in body_response.items():
            try:
                raw_email = get_body_bytes(data)

                if not raw_email:
                    print(f"邮件 UID={uid} 没有正文内容，跳过")
                    continue

                mail_date = uid_date_map.get(uid)

                parsed = parse_email(
                    uid,
                    raw_email,
                    mail_date
                )

                parsed["delivery_type"] = classify_delivery_type(
                    parsed,
                    username
                )

                original_size = uid_size_map.get(uid, 0)

                parsed["download_limited"] = bool(
                    original_size and original_size > max_email_bytes
                )
                parsed["original_size"] = original_size
                parsed["downloaded_size"] = len(raw_email)

                emails.append(parsed)

            except Exception as e:
                print(f"邮件解析失败 UID={uid}: {e}")

    print(f"最终成功读取邮件数量: {len(emails)}")
    return emails


if __name__ == "__main__":
    emails = fetch_today_emails()

    print(f"\n成功读取 {len(emails)} 封邮件\n")

    for mail in emails:
        print("=" * 80)
        print("UID:", mail["uid"])
        print("主题:", mail["subject"])
        print("时间:", mail["date"])
        print("投递类型:", mail.get("delivery_type"))
        print("原始大小:", mail.get("original_size"))
        print("下载大小:", mail.get("downloaded_size"))
        print("是否截断:", mail.get("download_limited"))
        print("正文预览:")
        print(mail["body"][:300])
