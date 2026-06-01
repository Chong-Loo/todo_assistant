def build_daily_push_text(report, active_todos):
    lines = []

    lines.append("【邮件摘要】")

    mail_summaries = report.get("mail_summaries", [])

    if not mail_summaries:
        lines.append("- 今日暂无邮件摘要")
    else:
        for item in mail_summaries:
            importance = item.get("importance", "normal")
            subject = item.get("subject", "")
            summary = item.get("summary", "")

            lines.append(f"- [{importance}] {subject}：{summary}")

    lines.append("")
    lines.append("【当前待办】")

    visible_todos = [
        todo for todo in active_todos
        if todo.get("status", "open") in {"open", "snoozed"}
    ]

    if not visible_todos:
        lines.append("- 暂无待办")
    else:
        for index, todo in enumerate(visible_todos, start=1):
            status = todo.get("status", "open")
            priority = todo.get("priority", "normal")
            title = todo.get("title", "")
            deadline = todo.get("deadline") or "无明确截止时间"
            reason = todo.get("reason", "")
            todo_id = todo.get("id", "")

            prefix = "暂缓" if status == "snoozed" else priority

            lines.append(
                f"{index}. [{prefix}] {title}｜截止：{deadline}｜ID：{todo_id}｜依据：{reason}"
            )

    return "\n".join(lines)