from __future__ import annotations

from datetime import datetime


ACTIVE_STATUSES = {"open", "snoozed"}


def parse_deadline(deadline: str | None) -> datetime | None:
    text = str(deadline or "").strip()
    if not text:
        return None

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt == "%Y-%m-%d":
                return parsed.replace(hour=23, minute=59, second=59)
            return parsed
        except ValueError:
            continue

    return None


def is_todo_overdue(todo: dict) -> bool:
    if todo.get("status", "open") not in ACTIVE_STATUSES:
        return False

    deadline = parse_deadline(todo.get("deadline"))
    if deadline is None:
        return False

    return deadline < datetime.now()
