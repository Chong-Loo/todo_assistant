import os
import sqlite3
from pathlib import Path


# 项目根目录（源码位置）
BASE_DIR = Path(__file__).resolve().parent.parent


def _default_user_data_dir() -> Path:
    # 优先使用环境变量覆盖数据目录
    env = os.environ.get("TODO_ASSISTANT_DATA_DIR")
    if env:
        return Path(env)

    # Windows 使用 %APPDATA%\todo_assistant
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "todo_assistant"
        return Path.home() / "AppData" / "Roaming" / "todo_assistant"

    # macOS 使用 ~/Library/Application Support/todo_assistant
    if os.uname().sysname == "Darwin":
        return Path.home() / "Library" / "Application Support" / "todo_assistant"

    # 其他类 Unix 系统使用 ~/.config/todo_assistant
    return Path.home() / ".config" / "todo_assistant"


# 默认数据目录（可被 TODO_ASSISTANT_DATA_DIR 环境变量覆盖）
DATA_DIR = _default_user_data_dir()

# 默认数据库路径
DB_PATH = DATA_DIR / "todo_assistant.db"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,

    title TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'open',

    source_type TEXT NOT NULL DEFAULT 'manual',
    source_email_id TEXT,
    source_subject TEXT,
    source_from TEXT,
    source_date TEXT,
    source_delivery_type TEXT DEFAULT 'manual',

    reason TEXT,
    content TEXT,
    note TEXT,

    source_mail_json TEXT,

    is_manual INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    cancelled_at TEXT,
    snooze_until TEXT
);

CREATE TABLE IF NOT EXISTS todo_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    todo_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    mime_type TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY(todo_id) REFERENCES todos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_todos_status
ON todos(status);

CREATE INDEX IF NOT EXISTS idx_todos_priority
ON todos(priority);

CREATE INDEX IF NOT EXISTS idx_todos_deadline
ON todos(deadline);

CREATE INDEX IF NOT EXISTS idx_todos_created_at
ON todos(created_at);

CREATE INDEX IF NOT EXISTS idx_todo_attachments_todo_id
ON todo_attachments(todo_id);
"""


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
    return {str(row["name"]) for row in rows}


def _ensure_column(conn, table_name: str, column_name: str, ddl: str):
    columns = _table_columns(conn, table_name)

    if column_name not in columns:
        conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl};"
        )


def init_db():
    """
    初始化数据库结构，可重复执行。

    兼容迁移：
    - 如果 todos 表是旧版本，会自动补 source_mail_json 字段，
      用于长期保存待办关联邮件正文快照。
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

        _ensure_column(
            conn,
            table_name="todos",
            column_name="source_mail_json",
            ddl="TEXT"
        )

        conn.execute("PRAGMA journal_mode = WAL;")
        conn.commit()


def get_db_path():
    return DB_PATH
