import uuid
from datetime import datetime


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_todo_key(todo):
    return (
        str(todo.get("title", "")).strip(),
        todo.get("deadline"),
        str(todo.get("source_email_id", ""))
    )


def build_todo_id(todo, index):
    source_date = str(todo.get("source_date") or todo.get("created_at") or "")
    date_part = source_date[:10].replace("-", "")

    if not date_part or len(date_part) != 8:
        date_part = datetime.now().strftime("%Y%m%d")

    return f"{date_part}-{index:03d}"


def ensure_unique_id(todo, index, seen_ids):
    current_id = str(todo.get("id", "")).strip()

    if current_id and current_id not in seen_ids:
        todo["id"] = current_id
        seen_ids.add(current_id)
        return todo

    base_id = build_todo_id(todo, index)
    candidate = base_id

    while candidate in seen_ids:
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{base_id}-{suffix}"

    todo["id"] = candidate
    seen_ids.add(candidate)
    return todo


def ensure_todo_fields(todo, index, seen_ids):
    todo = dict(todo)
    todo = ensure_unique_id(todo, index, seen_ids)

    todo.setdefault("status", "open")
    todo.setdefault("priority", "normal")
    todo.setdefault("created_at", now_str())
    todo.setdefault("updated_at", now_str())
    todo.setdefault("completed_at", None)
    todo.setdefault("cancelled_at", None)
    todo.setdefault("snooze_until", None)
    todo.setdefault("note", "")
    todo.setdefault("content", "")
    todo.setdefault("reason", "")
    todo.setdefault("source_mail", None)

    is_manual = bool(todo.get("is_manual"))
    todo["is_manual"] = is_manual

    if is_manual:
        todo.setdefault("source_type", "manual")
        todo.setdefault("source_email_id", "manual")
        todo.setdefault("source_subject", "")
        todo.setdefault("source_from", "")
        todo.setdefault("source_date", todo.get("created_at"))
        todo.setdefault("source_delivery_type", "manual")
    else:
        todo.setdefault("source_type", "email")
        todo.setdefault("source_email_id", "")
        todo.setdefault("source_subject", "")
        todo.setdefault("source_from", "")
        todo.setdefault("source_date", todo.get("created_at"))
        todo.setdefault("source_delivery_type", "other")

    return todo


def merge_todos(old_todos, new_todos):
    """
    合并规则：
    1. 保留 SQLite 中已有的全部待办，包括 open / snoozed / done / cancelled。
    2. 新待办加入，默认 open。
    3. title + deadline + source_email_id 去重。
    4. 如果新旧任务重复，保留旧任务，因为旧任务可能已有状态、备注、附件。
    5. 不再像 JSON 旧逻辑那样丢弃 done/cancelled，避免历史状态被每日任务覆盖。
    """
    result = []
    seen_keys = set()
    seen_ids = set()
    index = 1

    for todo in old_todos:
        todo = ensure_todo_fields(todo, index, seen_ids)
        index += 1

        key = make_todo_key(todo)

        if key in seen_keys:
            continue

        seen_keys.add(key)
        result.append(todo)

    for todo in new_todos:
        todo = ensure_todo_fields(todo, index, seen_ids)
        index += 1

        todo["status"] = "open"
        todo["updated_at"] = now_str()

        key = make_todo_key(todo)

        if key in seen_keys:
            continue

        seen_keys.add(key)
        result.append(todo)

    return sort_todos(result)


def sort_todos(todos):
    priority_order = {
        "urgent": 0,
        "high": 1,
        "normal": 2,
        "low": 3
    }

    status_order = {
        "open": 0,
        "snoozed": 1,
        "done": 2,
        "cancelled": 3
    }

    return sorted(
        todos,
        key=lambda x: (
            status_order.get(x.get("status", "open"), 0),
            priority_order.get(x.get("priority", "normal"), 2),
            x.get("deadline") or "9999-12-31 23:59",
            x.get("created_at") or ""
        )
    )
