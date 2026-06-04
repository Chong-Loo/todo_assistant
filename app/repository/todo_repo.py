import json
from datetime import datetime, timedelta
from typing import Any, Iterable

from app.db import get_connection


TODO_COLUMNS = [
    "id",
    "title",
    "priority",
    "deadline",
    "status",
    "source_type",
    "source_email_id",
    "source_subject",
    "source_from",
    "source_date",
    "source_delivery_type",
    "reason",
    "content",
    "note",
    "source_mail_json",
    "is_manual",
    "created_at",
    "updated_at",
    "completed_at",
    "cancelled_at",
    "snooze_until",
]


def _json_dumps_or_none(value: Any) -> str | None:
    if value is None:
        return None

    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return None


def _json_loads_or_none(value: Any):
    if not value:
        return None

    try:
        return json.loads(value)
    except Exception:
        return None


def _prepare_payload(todo: dict[str, Any]) -> dict[str, Any]:
    payload = {column: todo.get(column) for column in TODO_COLUMNS}

    if isinstance(todo.get("source_mail"), dict):
        payload["source_mail_json"] = _json_dumps_or_none(todo["source_mail"])
    elif payload.get("source_mail_json"):
        payload["source_mail_json"] = str(payload["source_mail_json"])
    else:
        payload["source_mail_json"] = None

    payload["is_manual"] = 1 if bool(todo.get("is_manual")) else 0

    return payload


def _row_to_dict(row) -> dict[str, Any]:
    data = dict(row)
    source_mail_json = data.pop("source_mail_json", None)

    data["source_mail"] = _json_loads_or_none(source_mail_json)
    data["is_manual"] = bool(data.get("is_manual"))

    return data


def insert_todo(todo: dict[str, Any]) -> dict[str, Any]:
    payload = _prepare_payload(todo)

    placeholders = ", ".join("?" for _ in TODO_COLUMNS)
    columns_sql = ", ".join(TODO_COLUMNS)

    with get_connection() as conn:
        conn.execute(
            f"""
            INSERT INTO todos ({columns_sql})
            VALUES ({placeholders})
            """,
            [payload[column] for column in TODO_COLUMNS],
        )
        conn.commit()

    result = get_todo_by_id(str(todo["id"]))
    if result is None:
        raise RuntimeError(f"新增后未能读取待办 ID: {todo['id']}")

    return result


def upsert_todo(todo: dict[str, Any]) -> dict[str, Any]:
    """
    若 id 已存在则更新，否则新增。
    main.py 保存合并后的待办时使用。
    """
    payload = _prepare_payload(todo)

    update_columns = [
        column for column in TODO_COLUMNS
        if column != "id"
    ]

    update_sql = ", ".join(
        f"{column}=excluded.{column}"
        for column in update_columns
    )

    placeholders = ", ".join("?" for _ in TODO_COLUMNS)
    columns_sql = ", ".join(TODO_COLUMNS)

    with get_connection() as conn:
        conn.execute(
            f"""
            INSERT INTO todos ({columns_sql})
            VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET
                {update_sql}
            """,
            [payload[column] for column in TODO_COLUMNS],
        )
        conn.commit()

    result = get_todo_by_id(str(todo["id"]))
    if result is None:
        raise RuntimeError(f"写入后未能读取待办 ID: {todo['id']}")

    return result


def get_todo_by_id(todo_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()

    return _row_to_dict(row) if row else None


def list_todos(
    statuses: Iterable[str] | None = None,
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM todos"
    conditions: list[str] = []
    params: list[Any] = []

    if statuses:
        statuses = list(statuses)
        placeholders = ", ".join("?" for _ in statuses)
        conditions.append(f"status IN ({placeholders})")
        params.extend(statuses)

    if source_type:
        conditions.append("source_type = ?")
        params.append(source_type)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += """
        ORDER BY
            CASE status
                WHEN 'open' THEN 0
                WHEN 'snoozed' THEN 1
                WHEN 'done' THEN 2
                ELSE 3
            END,
            CASE priority
                WHEN 'urgent' THEN 0
                WHEN 'high' THEN 1
                WHEN 'normal' THEN 2
                ELSE 3
            END,
            CASE WHEN deadline IS NULL OR deadline = '' THEN 1 ELSE 0 END,
            deadline ASC,
            created_at DESC
    """

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_dict(row) for row in rows]


def update_todo_fields(todo_id: str, **fields: Any) -> dict[str, Any]:
    if not fields:
        todo = get_todo_by_id(todo_id)
        if todo is None:
            raise RuntimeError(f"没有找到待办 ID: {todo_id}")
        return todo

    fields["updated_at"] = fields.get(
        "updated_at",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    if "source_mail" in fields:
        source_mail = fields.pop("source_mail")
        fields["source_mail_json"] = _json_dumps_or_none(source_mail)

    if "is_manual" in fields:
        fields["is_manual"] = 1 if bool(fields["is_manual"]) else 0

    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [todo_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE todos SET {assignments} WHERE id = ?",
            values,
        )
        conn.commit()

    if cursor.rowcount == 0:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    todo = get_todo_by_id(todo_id)
    if todo is None:
        raise RuntimeError(f"更新后未能读取待办 ID: {todo_id}")

    return todo


def complete_all_todos(statuses: tuple[str, ...]) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE status IN ({})".format(
                ", ".join("?" for _ in statuses)
            ),
            statuses,
        ).fetchall()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE todos SET status = 'done', completed_at = ?, updated_at = ? WHERE status IN ({})".format(
                ", ".join("?" for _ in statuses)
            ),
            (now, now) + statuses,
        )
        conn.commit()

    return [_row_to_dict(row) for row in rows]


def delete_all_done() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE status = 'done'"
        ).fetchall()

        conn.execute("DELETE FROM todos WHERE status = 'done'")
        conn.commit()

    return [_row_to_dict(row) for row in rows]


def delete_todo(todo_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM todos WHERE id = ?",
            (todo_id,),
        )
        conn.commit()

    if cursor.rowcount == 0:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    return True


def cleanup_completed_todos(
    keep_days: int = 3,
    keep_count: int = 30,
) -> list[str]:
    """
    清理已完成待办：
    1. 完成时间超过 keep_days 的 done 待办；
    2. 即使未过期，也只保留最近 keep_count 条 done 待办。

    返回被删除的 todo_id，供上层删除磁盘附件目录。
    """
    cutoff = datetime.now() - timedelta(days=keep_days)
    cutoff_text = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, completed_at, updated_at
            FROM todos
            WHERE status = 'done'
            ORDER BY COALESCE(completed_at, updated_at) DESC
            """
        ).fetchall()

        delete_ids: list[str] = []

        for index, row in enumerate(rows):
            todo_id = str(row["id"])
            completed_at = row["completed_at"] or row["updated_at"] or ""

            should_keep_by_count = index < keep_count
            should_keep_by_time = bool(completed_at and completed_at >= cutoff_text)

            if not (should_keep_by_count and should_keep_by_time):
                delete_ids.append(todo_id)

        if delete_ids:
            placeholders = ", ".join("?" for _ in delete_ids)
            conn.execute(
                f"DELETE FROM todos WHERE id IN ({placeholders})",
                delete_ids,
            )
            conn.commit()

    return delete_ids
