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
    if notification is None:
        # plyer 平台通知不可用（可能在打包时未包含），降级为打印日志
        print("通知（plyer 未加载）：", message)
        return

    try:
        notification.notify(
            title="智能待办助手",
            message=message,
            timeout=10
        )
    except Exception:
        # 通知失败时不阻塞主流程
        print("通知发送失败。")