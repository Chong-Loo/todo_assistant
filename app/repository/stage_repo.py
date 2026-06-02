from typing import Any

from app.db import get_connection


STAGE_COLUMNS = [
    "id",
    "todo_id",
    "title",
    "deadline",
    "status",
    "sort_order",
    "created_at",
    "completed_at",
]


def _row_to_dict(row) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def insert_stage(
    *,
    todo_id: str,
    title: str,
    deadline: str | None,
    sort_order: int,
    created_at: str,
) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO todo_stages (todo_id, title, deadline, status, sort_order, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (todo_id, title, deadline, sort_order, created_at),
        )
        conn.commit()
        stage_id = cursor.lastrowid

    stage = get_stage_by_id(int(stage_id))
    if stage is None:
        raise RuntimeError("阶段记录已写入，但读取失败")

    return stage


def get_stage_by_id(stage_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM todo_stages WHERE id = ?",
            (stage_id,),
        ).fetchone()

    return _row_to_dict(row) if row else None


def list_stages(todo_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM todo_stages
            WHERE todo_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (todo_id,),
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def update_stage_fields(stage_id: int, **fields: Any) -> dict[str, Any]:
    if not fields:
        stage = get_stage_by_id(stage_id)
        if stage is None:
            raise RuntimeError(f"没有找到阶段 ID: {stage_id}")
        return stage

    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [stage_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE todo_stages SET {assignments} WHERE id = ?",
            values,
        )
        conn.commit()

    if cursor.rowcount == 0:
        raise RuntimeError(f"没有找到阶段 ID: {stage_id}")

    stage = get_stage_by_id(stage_id)
    if stage is None:
        raise RuntimeError(f"更新后未能读取阶段 ID: {stage_id}")

    return stage


def delete_stage(stage_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM todo_stages WHERE id = ?",
            (stage_id,),
        )
        conn.commit()

    if cursor.rowcount == 0:
        raise RuntimeError(f"没有找到阶段 ID: {stage_id}")

    return True
