from typing import Any

from app.db import get_connection


def _row_to_dict(row) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def insert_attachment_record(
    *,
    todo_id: str,
    filename: str,
    stored_name: str,
    file_path: str,
    file_size: int,
    mime_type: str | None,
    created_at: str,
) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO todo_attachments (
                todo_id,
                filename,
                stored_name,
                file_path,
                file_size,
                mime_type,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                todo_id,
                filename,
                stored_name,
                file_path,
                file_size,
                mime_type,
                created_at,
            ),
        )
        conn.commit()
        attachment_id = cursor.lastrowid

    attachment = get_attachment_by_id(int(attachment_id))
    if attachment is None:
        raise RuntimeError("附件记录已写入，但读取失败")

    return attachment


def get_attachment_by_id(attachment_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM todo_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()

    return _row_to_dict(row) if row else None


def list_attachments(todo_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM todo_attachments
            WHERE todo_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (todo_id,),
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def delete_attachment_by_path(
    todo_id: str,
    file_path: str,
) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM todo_attachments
            WHERE todo_id = ? AND file_path = ?
            """,
            (todo_id, file_path),
        ).fetchone()

        if row is None:
            return None

        conn.execute(
            """
            DELETE FROM todo_attachments
            WHERE todo_id = ? AND file_path = ?
            """,
            (todo_id, file_path),
        )
        conn.commit()

    return _row_to_dict(row)


def delete_all_attachment_records(todo_id: str) -> list[dict[str, Any]]:
    attachments = list_attachments(todo_id)

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM todo_attachments WHERE todo_id = ?",
            (todo_id,),
        )
        conn.commit()

    return attachments
