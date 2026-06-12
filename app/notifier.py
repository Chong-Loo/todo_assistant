try:
    from plyer import notification
except Exception:
    notification = None


def build_notification_message(report, active_todos):
    mail_count = report.get("mail_count", 0)
    todo_count = len(active_todos)

    urgent_count = sum(
        1 for todo in active_todos
        if todo.get("priority") == "urgent"
        and todo.get("status", "open") in {"open", "snoozed"}
    )

    high_count = sum(
        1 for todo in active_todos
        if todo.get("priority") == "high"
        and todo.get("status", "open") in {"open", "snoozed"}
    )

    return (
        f"读取 {mail_count} 封邮件，"
        f"当前待办 {todo_count} 个，"
        f"紧急 {urgent_count} 个，高优先级 {high_count} 个。"
    )


def notify_daily_summary(report, active_todos):
    message = build_notification_message(report, active_todos)

    from app.settings import load_config
    config = load_config()
    notif_cfg = config.get("app", {}).get("notification", {})
    if not notif_cfg.get("enabled", True):
        return
    duration = int(notif_cfg.get("duration", 10))

    notify_message("智能待办助手", message, timeout=duration)


def notify_message(title: str, message: str, timeout: int = 10):
    if notification is None:
        print(f"通知（plyer 未加载）：{message}")
        return

    try:
        notification.notify(title=title, message=message, timeout=timeout)
    except Exception:
        print("通知发送失败。")