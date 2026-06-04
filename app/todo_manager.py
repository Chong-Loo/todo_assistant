import argparse
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.db import init_db, DATA_DIR
from app.repository import attachment_repo, stage_repo, todo_repo


BASE_DIR = Path(__file__).resolve().parent.parent
ATTACHMENT_DIR = DATA_DIR / "todo_attachments"


VALID_STATUS = {
    "open",
    "done",
    "cancelled",
    "snoozed"
}

VALID_PRIORITIES = {
    "urgent",
    "high",
    "normal",
    "low"
}


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sanitize_filename(filename):
    filename = Path(str(filename or "attachment")).name.strip()
    if not filename:
        filename = "attachment"

    cleaned = re.sub(r'[\\/:*?"<>|\r\n]+', "_", filename)
    cleaned = cleaned.strip(" .")

    return cleaned or "attachment"


def safe_todo_dir_name(todo_id):
    safe_todo_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(todo_id or "unknown"))
    return safe_todo_id.strip("_") or "unknown"


def build_attachment_storage_path(todo_id, filename):
    attachment_dir = ATTACHMENT_DIR / safe_todo_dir_name(todo_id)
    attachment_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(filename)
    target_path = attachment_dir / safe_name

    if target_path.exists():
        stem = target_path.stem
        suffix = target_path.suffix
        unique_suffix = uuid.uuid4().hex[:6]
        target_path = attachment_dir / f"{stem}-{unique_suffix}{suffix}"

    try:
        relative_path = target_path.relative_to(DATA_DIR).as_posix()
    except Exception:
        # fallback to absolute posix path when relative conversion fails
        relative_path = target_path.as_posix()
    return target_path, relative_path


def create_manual_todo_id():
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"manual-{now}-{suffix}"


def attachment_record_to_ui(attachment: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": attachment.get("id"),
        "name": attachment.get("filename", "未命名文件"),
        "path": attachment.get("file_path", ""),
        "size": attachment.get("file_size", 0),
        "mime_type": attachment.get("mime_type"),
        "uploaded_at": attachment.get("created_at", ""),
    }


def _stage_record_to_ui(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "todo_id": record["todo_id"],
        "title": record["title"],
        "deadline": record.get("deadline"),
        "status": record["status"],
        "sort_order": record["sort_order"],
        "created_at": record["created_at"],
        "completed_at": record.get("completed_at"),
    }


def hydrate_todo(todo: dict[str, Any]) -> dict[str, Any]:
    hydrated = dict(todo)
    todo_id = str(hydrated.get("id", ""))

    hydrated["is_manual"] = bool(hydrated.get("is_manual"))
    hydrated["attachments"] = [
        attachment_record_to_ui(attachment)
        for attachment in attachment_repo.list_attachments(todo_id)
    ]
    hydrated["stages"] = [
        _stage_record_to_ui(stage)
        for stage in stage_repo.list_stages(todo_id)
    ]

    return hydrated


def delete_attachment_directory(todo_id: str):
    todo_attachment_dir = ATTACHMENT_DIR / safe_todo_dir_name(todo_id)

    try:
        if todo_attachment_dir.exists():
            shutil.rmtree(todo_attachment_dir)
    except Exception:
        pass


def cleanup_completed_todos(keep_days=3, keep_count=30):
    init_db()
    deleted_ids = todo_repo.cleanup_completed_todos(
        keep_days=keep_days,
        keep_count=keep_count
    )

    for todo_id in deleted_ids:
        delete_attachment_directory(todo_id)

    return deleted_ids


def load_normalized_todos(cleanup=True):
    init_db()

    if cleanup:
        cleanup_completed_todos(
            keep_days=3,
            keep_count=30
        )

    return [
        hydrate_todo(todo)
        for todo in todo_repo.list_todos()
    ]


def find_todo(todos, todo_id):
    for todo in todos:
        if str(todo.get("id")) == str(todo_id):
            return todo

    return None


def get_todo(todo_id):
    init_db()
    todo = todo_repo.get_todo_by_id(str(todo_id))

    if todo is None:
        return None

    return hydrate_todo(todo)


def format_todo(todo):
    todo_id = todo.get("id", "")
    status = todo.get("status", "open")
    priority = todo.get("priority", "normal")
    title = todo.get("title", "")
    deadline = todo.get("deadline") or "无明确截止时间"
    note = todo.get("note", "")
    snooze_until = todo.get("snooze_until")

    lines = [
        "-" * 80,
        f"ID: {todo_id}",
        f"状态: {status}",
        f"优先级: {priority}",
        f"标题: {title}",
        f"截止: {deadline}",
    ]

    if todo.get("is_manual"):
        lines.append(f"具体内容: {todo.get('content', '')}")
    else:
        lines.append(f"来源: {todo.get('source_subject', '')}")
        lines.append(f"依据: {todo.get('reason', '')}")

    if snooze_until:
        lines.append(f"暂缓到: {snooze_until}")

    if note:
        lines.append(f"备注: {note}")

    attachments = todo.get("attachments", [])
    if attachments:
        lines.append(f"附件数量: {len(attachments)}")

    return "\n".join(lines)


def list_todos(status=None, show_all=False):
    todos = load_normalized_todos()

    if not show_all:
        visible_status = {"open", "snoozed"}
    else:
        visible_status = VALID_STATUS

    if status:
        visible_status = {status}

    filtered = [
        todo for todo in todos
        if todo.get("status", "open") in visible_status
    ]

    if not filtered:
        print("没有匹配的待办。")
        return

    for todo in filtered:
        print(format_todo(todo))


def update_status(todo_id, status, note=None, snooze_until=None):
    if status not in VALID_STATUS:
        raise ValueError(f"非法状态: {status}")

    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    updates = {
        "status": status,
        "updated_at": now_str(),
    }

    if note is not None:
        updates["note"] = note

    if status == "done":
        updates["completed_at"] = now_str()
        updates["cancelled_at"] = None
        updates["snooze_until"] = None

    elif status == "cancelled":
        updates["cancelled_at"] = now_str()
        updates["completed_at"] = None
        updates["snooze_until"] = None

    elif status == "snoozed":
        if not snooze_until:
            raise RuntimeError("暂缓任务必须提供 --until 参数，例如 2026-05-10 09:00")

        updates["snooze_until"] = snooze_until
        updates["completed_at"] = None
        updates["cancelled_at"] = None

    elif status == "open":
        updates["completed_at"] = None
        updates["cancelled_at"] = None
        updates["snooze_until"] = None

    todo_repo.update_todo_fields(str(todo_id), **updates)

    cleanup_completed_todos(
        keep_days=3,
        keep_count=30
    )

    updated = get_todo(todo_id)
    if updated is None:
        raise RuntimeError(f"更新后未能读取待办 ID: {todo_id}")

    return updated


def update_priority(todo_id, priority):
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"非法优先级: {priority}")

    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    todo_repo.update_todo_fields(
        str(todo_id),
        priority=priority,
        updated_at=now_str()
    )

    updated = get_todo(todo_id)
    if updated is None:
        raise RuntimeError(f"更新后未能读取待办 ID: {todo_id}")

    return updated


def update_deadline(todo_id, deadline):
    """
    修改待办截止时间。

    deadline:
    - None / "" 表示清除截止时间
    - 支持 YYYY-MM-DD
    - 支持 YYYY-MM-DD HH:mm
    - 支持 YYYY-MM-DD HH:mm:ss
    """
    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    normalized_deadline = None

    if deadline:
        text = str(deadline).strip()
        parsed = None

        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d"
        ):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue

        if parsed is None:
            raise ValueError(
                "截止时间格式错误，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm"
            )

        if len(text) == 10:
            normalized_deadline = parsed.strftime("%Y-%m-%d")
        else:
            normalized_deadline = parsed.strftime("%Y-%m-%d %H:%M")

    todo_repo.update_todo_fields(
        str(todo_id),
        deadline=normalized_deadline,
        updated_at=now_str()
    )

    updated = get_todo(todo_id)
    if updated is None:
        raise RuntimeError(f"更新后未能读取待办 ID: {todo_id}")

    return updated


def add_note(todo_id, note):
    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    todo_repo.update_todo_fields(
        str(todo_id),
        note=note,
        updated_at=now_str()
    )

    updated = get_todo(todo_id)
    if updated is None:
        raise RuntimeError(f"更新后未能读取待办 ID: {todo_id}")

    return updated


def list_stages(todo_id: str) -> list[dict[str, Any]]:
    init_db()
    return [
        _stage_record_to_ui(stage)
        for stage in stage_repo.list_stages(str(todo_id))
    ]


def add_stage(
    todo_id: str,
    title: str,
    deadline: str | None = None,
) -> dict[str, Any]:
    init_db()
    cur_stages = stage_repo.list_stages(str(todo_id))
    sort_order = len(cur_stages)
    now = now_str()

    stage = stage_repo.insert_stage(
        todo_id=str(todo_id),
        title=title.strip(),
        deadline=deadline,
        sort_order=sort_order,
        created_at=now,
    )

    todo_repo.update_todo_fields(
        str(todo_id),
        updated_at=now,
    )

    return _stage_record_to_ui(stage)


def update_stage_status(stage_id: int, status: str) -> dict[str, Any]:
    init_db()
    if status not in ("pending", "done"):
        raise ValueError(f"非法阶段状态: {status}")

    updates: dict[str, Any] = {"status": status}
    if status == "done":
        updates["completed_at"] = now_str()
    else:
        updates["completed_at"] = None

    stage = stage_repo.update_stage_fields(stage_id, **updates)

    todo_repo.update_todo_fields(
        str(stage["todo_id"]),
        updated_at=now_str(),
    )

    return _stage_record_to_ui(stage)


def delete_stage(stage_id: int) -> bool:
    init_db()
    stage = stage_repo.get_stage_by_id(stage_id)
    if stage is None:
        raise RuntimeError(f"没有找到阶段 ID: {stage_id}")

    todo_id = str(stage["todo_id"])
    stage_repo.delete_stage(stage_id)

    remaining = stage_repo.list_stages(todo_id)
    for i, s in enumerate(remaining):
        if s["sort_order"] != i:
            stage_repo.update_stage_fields(s["id"], sort_order=i)

    todo_repo.update_todo_fields(
        todo_id,
        updated_at=now_str(),
    )

    return True


def add_manual_todo(
    title,
    priority="normal",
    deadline=None,
    content="",
    note=""
):
    init_db()

    if priority not in VALID_PRIORITIES:
        priority = "normal"

    now = now_str()
    normalized_content = str(content or "").strip()

    todo = {
        "id": create_manual_todo_id(),
        "title": str(title).strip(),
        "priority": priority,
        "deadline": deadline or None,
        "status": "open",

        "source_type": "manual",
        "source_email_id": "manual",
        "source_subject": "",
        "source_from": "",
        "source_date": now,
        "source_delivery_type": "manual",

        "reason": normalized_content,
        "content": normalized_content,
        "note": note or "",
        "source_mail": None,

        "is_manual": True,

        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "cancelled_at": None,
        "snooze_until": None,
    }

    if not todo["title"]:
        raise RuntimeError("待办标题不能为空")

    todo_repo.insert_todo(todo)

    created = get_todo(todo["id"])
    if created is None:
        raise RuntimeError("待办已写入，但读取失败")

    return created


def edit_manual_todo(
    todo_id: str,
    *,
    title: str | None = None,
    priority: str | None = None,
    deadline: str | None | bool = None,
    content: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    init_db()
    current = get_todo(todo_id)
    if current is None:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")
    if not current.get("is_manual"):
        raise RuntimeError("只能编辑人工待办")

    updates: dict[str, Any] = {}
    if title is not None:
        updates["title"] = title.strip()
    if priority is not None:
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"非法优先级: {priority}")
        updates["priority"] = priority
    if deadline is not False:
        updates["deadline"] = deadline
    elif deadline is None:
        updates["deadline"] = None
    if content is not None:
        normalized = str(content).strip()
        updates["content"] = normalized
        updates["reason"] = normalized
    if note is not None:
        updates["note"] = note

    if not updates:
        return current

    todo_repo.update_todo_fields(todo_id, **updates)

    updated = get_todo(todo_id)
    if updated is None:
        raise RuntimeError("更新后未能读取待办")

    return updated


def add_todo_attachment(todo_id, filename, content):
    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    if hasattr(content, "tobytes"):
        content = content.tobytes()
    elif isinstance(content, memoryview):
        content = content.tobytes()
    elif not isinstance(content, (bytes, bytearray)):
        content = bytes(content)

    target_path, relative_path = build_attachment_storage_path(todo_id, filename)
    target_path.write_bytes(bytes(content))

    attachment = attachment_repo.insert_attachment_record(
        todo_id=str(todo_id),
        filename=sanitize_filename(filename),
        stored_name=target_path.name,
        file_path=relative_path,
        file_size=len(content),
        mime_type=None,
        created_at=now_str()
    )

    todo_repo.update_todo_fields(
        str(todo_id),
        updated_at=now_str()
    )

    return attachment_record_to_ui(attachment)


def delete_todo_attachment(todo_id, attachment_path):
    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    removed = attachment_repo.delete_attachment_by_path(
        str(todo_id),
        str(attachment_path)
    )

    if removed is None:
        raise RuntimeError("没有找到对应附件")

    file_path = DATA_DIR / str(removed.get("file_path", ""))

    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass

    todo_repo.update_todo_fields(
        str(todo_id),
        updated_at=now_str()
    )

    return True


def complete_all_todos(source_type: str | None = None) -> int:
    init_db()
    if source_type == "manual":
        todos = todo_repo.list_todos()
        target_ids = [
            t["id"] for t in todos
            if t["status"] in ("open", "snoozed") and t.get("is_manual")
        ]
    elif source_type == "email":
        todos = todo_repo.list_todos()
        target_ids = [
            t["id"] for t in todos
            if t["status"] in ("open", "snoozed") and not t.get("is_manual")
        ]
    else:
        done_list = todo_repo.complete_all_todos(("open", "snoozed"))
        target_ids = [t["id"] for t in done_list]

    now = now_str()
    count = 0
    for tid in target_ids:
        todo_repo.update_todo_fields(tid, status="done", completed_at=now, updated_at=now)
        count += 1

    cleanup_completed_todos(keep_days=3, keep_count=30)
    return count


def clear_all_completed_todos() -> int:
    init_db()
    done_list = todo_repo.delete_all_done()
    count = len(done_list)
    for todo in done_list:
        delete_attachment_directory(str(todo["id"]))
    return count


def delete_todo(todo_id):
    current = get_todo(todo_id)

    if not current:
        raise RuntimeError(f"没有找到待办 ID: {todo_id}")

    delete_attachment_directory(str(todo_id))
    todo_repo.delete_todo(str(todo_id))

    return True


def build_parser():
    parser = argparse.ArgumentParser(
        description="待办状态管理工具"
    )

    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="查看待办")
    list_parser.add_argument("--status", choices=list(VALID_STATUS))
    list_parser.add_argument("--all", action="store_true")

    done_parser = subparsers.add_parser("done", help="标记完成")
    done_parser.add_argument("todo_id")
    done_parser.add_argument("--note", default=None)

    cancel_parser = subparsers.add_parser("cancel", help="取消待办")
    cancel_parser.add_argument("todo_id")
    cancel_parser.add_argument("--note", default=None)

    snooze_parser = subparsers.add_parser("snooze", help="暂缓待办")
    snooze_parser.add_argument("todo_id")
    snooze_parser.add_argument("--until", required=True)
    snooze_parser.add_argument("--note", default=None)

    reopen_parser = subparsers.add_parser("reopen", help="重新打开待办")
    reopen_parser.add_argument("todo_id")
    reopen_parser.add_argument("--note", default=None)

    note_parser = subparsers.add_parser("note", help="添加或修改备注")
    note_parser.add_argument("todo_id")
    note_parser.add_argument("note")

    priority_parser = subparsers.add_parser("priority", help="修改优先级")
    priority_parser.add_argument("todo_id")
    priority_parser.add_argument("priority", choices=list(VALID_PRIORITIES))

    deadline_parser = subparsers.add_parser("deadline", help="修改截止时间")
    deadline_parser.add_argument("todo_id")
    deadline_parser.add_argument("deadline", nargs="?", default="")

    delete_parser = subparsers.add_parser("delete", help="删除待办")
    delete_parser.add_argument("todo_id")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        list_todos(
            status=args.status,
            show_all=args.all
        )

    elif args.command == "done":
        todo = update_status(args.todo_id, "done", note=args.note)
        print("更新成功：")
        print(format_todo(todo))

    elif args.command == "cancel":
        todo = update_status(args.todo_id, "cancelled", note=args.note)
        print("更新成功：")
        print(format_todo(todo))

    elif args.command == "snooze":
        todo = update_status(
            args.todo_id,
            "snoozed",
            note=args.note,
            snooze_until=args.until
        )
        print("更新成功：")
        print(format_todo(todo))

    elif args.command == "reopen":
        todo = update_status(args.todo_id, "open", note=args.note)
        print("更新成功：")
        print(format_todo(todo))

    elif args.command == "note":
        todo = add_note(args.todo_id, args.note)
        print("备注已更新：")
        print(format_todo(todo))

    elif args.command == "priority":
        todo = update_priority(args.todo_id, args.priority)
        print("优先级已更新：")
        print(format_todo(todo))

    elif args.command == "deadline":
        todo = update_deadline(args.todo_id, args.deadline)
        print("截止时间已更新：")
        print(format_todo(todo))

    elif args.command == "delete":
        delete_todo(args.todo_id)
        print(f"已删除待办: {args.todo_id}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
