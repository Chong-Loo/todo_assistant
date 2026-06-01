from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.db import init_db
from app.repository.todo_repo import upsert_todo
from app.repository import attachment_repo

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCE_JSON = DATA_DIR / "active_todos.json"
BACKUP_DIR = DATA_DIR / "backup_json"

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else {"todos": []}

def normalize(todo: dict[str, Any]) -> dict[str, Any]:
    now = now_str()
    item = dict(todo)
    todo_id = str(item.get("id") or "").strip()
    if not todo_id:
        todo_id = f"migrated-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    is_manual = bool(item.get("is_manual"))
    reason = str(item.get("reason") or "").strip()
    content = str(item.get("content") or "").strip() or (reason if is_manual else "")
    return {
        "id": todo_id,
        "title": str(item.get("title") or "未命名待办").strip(),
        "priority": item.get("priority") or "normal",
        "deadline": item.get("deadline") or None,
        "status": item.get("status") or "open",
        "source_type": "manual" if is_manual else "email",
        "source_email_id": item.get("source_email_id") or ("manual" if is_manual else ""),
        "source_subject": item.get("source_subject") or "",
        "source_from": item.get("source_from") or "",
        "source_date": item.get("source_date") or item.get("created_at") or now,
        "source_delivery_type": item.get("source_delivery_type") or ("manual" if is_manual else "other"),
        "reason": reason,
        "content": content,
        "note": item.get("note") or "",
        "source_mail": item.get("source_mail") if isinstance(item.get("source_mail"), dict) else None,
        "is_manual": is_manual,
        "created_at": item.get("created_at") or now,
        "updated_at": item.get("updated_at") or now,
        "completed_at": item.get("completed_at"),
        "cancelled_at": item.get("cancelled_at"),
        "snooze_until": item.get("snooze_until"),
    }

def backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKUP_DIR / f"active_todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(SOURCE_JSON, path)
    return path

def attachment_exists(todo_id: str, file_path: str) -> bool:
    return any(str(x.get("file_path") or "") == file_path for x in attachment_repo.list_attachments(todo_id))

def migrate_attachments(todo_id: str, attachments: list[dict[str, Any]]) -> int:
    count = 0
    for item in attachments:
        rel = str(item.get("path") or "").strip()
        if not rel:
            continue
        abs_path = BASE_DIR / rel
        if not abs_path.exists() or attachment_exists(todo_id, rel):
            continue
        attachment_repo.insert_attachment_record(
            todo_id=todo_id,
            filename=str(item.get("name") or abs_path.name),
            stored_name=abs_path.name,
            file_path=rel,
            file_size=int(item.get("size") or abs_path.stat().st_size),
            mime_type=item.get("mime_type"),
            created_at=str(item.get("uploaded_at") or now_str()),
        )
        count += 1
    return count

def main():
    init_db()
    if not SOURCE_JSON.exists():
        print(f"未找到旧待办文件：{SOURCE_JSON}")
        return
    data = load_json(SOURCE_JSON)
    todos = data if isinstance(data, list) else data.get("todos", [])
    if not isinstance(todos, list):
        raise RuntimeError("active_todos.json 格式不正确：todos 不是列表")
    print(f"旧 JSON 已备份：{backup()}")
    todo_count = 0
    attachment_count = 0
    for todo in todos:
        if not isinstance(todo, dict):
            continue
        normalized = normalize(todo)
        upsert_todo(normalized)
        todo_count += 1
        attachments = todo.get("attachments") or []
        if isinstance(attachments, list):
            attachment_count += migrate_attachments(normalized["id"], attachments)
    print("迁移完成")
    print(f"待办写入数量：{todo_count}")
    print(f"附件记录写入数量：{attachment_count}")

if __name__ == "__main__":
    main()
