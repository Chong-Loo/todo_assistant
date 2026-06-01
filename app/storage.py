import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.db import init_db
from app.repository.todo_repo import upsert_todo
from app.todo_manager import load_normalized_todos


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = DATA_DIR / "daily_reports"


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def save_daily_report(report_date: date, data: dict):
    ensure_dirs()

    path = REPORT_DIR / f"{report_date}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_todo_for_db(todo: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item = dict(todo)

    item.setdefault("priority", "normal")
    item.setdefault("deadline", None)
    item.setdefault("status", "open")
    item.setdefault("created_at", now)
    item.setdefault("updated_at", now)
    item.setdefault("completed_at", None)
    item.setdefault("cancelled_at", None)
    item.setdefault("snooze_until", None)
    item.setdefault("note", "")
    item.setdefault("content", "")
    item.setdefault("reason", "")
    item.setdefault("source_mail", None)

    is_manual = bool(item.get("is_manual"))
    item["is_manual"] = is_manual

    if is_manual:
        item.setdefault("source_type", "manual")
        item.setdefault("source_email_id", "manual")
        item.setdefault("source_subject", "")
        item.setdefault("source_from", "")
        item.setdefault("source_date", item.get("created_at", now))
        item.setdefault("source_delivery_type", "manual")
    else:
        item.setdefault("source_type", "email")
        item.setdefault("source_email_id", "")
        item.setdefault("source_subject", "")
        item.setdefault("source_from", "")
        item.setdefault("source_date", item.get("created_at", now))
        item.setdefault("source_delivery_type", "other")

    return item


def load_active_todos():
    """
    兼容 main.py 旧调用名。
    实际返回 SQLite 中的全部待办，由 todo_merger 决定如何合并。
    """
    init_db()
    return load_normalized_todos(cleanup=True)


def save_active_todos(todos):
    """
    兼容 main.py 旧调用名。
    实际将待办逐条 upsert 到 SQLite。
    不再写 active_todos.json。
    """
    init_db()
    ensure_dirs()

    for todo in todos:
        normalized = _normalize_todo_for_db(todo)
        upsert_todo(normalized)
