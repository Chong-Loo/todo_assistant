from datetime import date

from app.mail_reader import fetch_new_emails, fetch_today_emails
from app.email_tracker import get_fetched_uids, record_fetched_emails
from app.settings import load_config
from app.todo_extractor import extract_todos_from_emails
from app.storage import (
    save_daily_report,
    load_active_todos,
    save_active_todos
)
from app.todo_merger import merge_todos
from app.push_builder import build_daily_push_text
from app.notifier import notify_daily_summary
from app.logger import setup_logger

logger = setup_logger()


def run_daily_job(lookback_days=None, on_progress=None, stop_check=None):
    today = date.today()

    logger.info("开始读取邮件")

    if lookback_days is None or lookback_days == 0:
        emails = fetch_new_emails()
        mode = "incremental"
    else:
        emails = fetch_today_emails(lookback_days=lookback_days)
        mode = "lookback"
        config = load_config()
        mail_cfg = config.get("mail", {})
        username = str(mail_cfg.get("username", ""))
        mailbox = str(mail_cfg.get("folder", "INBOX"))

        existing_uids = get_fetched_uids(username, mailbox)
        if existing_uids:
            before = len(emails)
            emails = [m for m in emails if int(m.get("uid", 0)) not in existing_uids]
            logger.info(f"按天模式过滤已处理邮件: {before} -> {len(emails)}")

        record_fetched_emails(emails, username=username, mailbox=mailbox)

    logger.info(f"读取邮件完成（模式={mode}），数量: {len(emails)}")

    logger.info("开始分析邮件")
    report = extract_todos_from_emails(emails, on_progress=on_progress, stop_check=stop_check)

    new_todos = report.get("todos", [])
    logger.info(f"邮件分析完成，新增待办数量: {len(new_todos)}")

    logger.info("读取历史待办")
    old_todos = load_active_todos()

    logger.info("合并待办")
    merged_todos = merge_todos(old_todos, new_todos)

    active_todos_for_push = [
        todo for todo in merged_todos
        if todo.get("status", "open") in {"open", "snoozed"}
    ]

    push_text = build_daily_push_text(report, active_todos_for_push)

    report["active_todos"] = active_todos_for_push
    report["final_push_text"] = push_text
    report["lookback_days"] = lookback_days

    save_daily_report(today, report)
    save_active_todos(merged_todos)

    if not report.get("cancelled"):
        notify_daily_summary(report, active_todos_for_push)

    logger.info("任务执行完成")
    logger.info("\n" + push_text)

    print("\n===== 今日推送内容 =====\n")
    print(push_text)


if __name__ == "__main__":
    run_daily_job()
