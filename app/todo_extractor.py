from pathlib import Path
import sys
import os

from app.llm_client import call_llm_json


BASE_DIR = Path(__file__).resolve().parent.parent

# Resolve prompt path robustly to work in development and frozen builds
def _resolve_prompt_path() -> Path:
    # 1. explicit env override
    env = os.environ.get("TODO_ASSISTANT_PROMPT_PATH")
    if env:
        p = Path(env)
        if p.exists():
            return p

    # 2. package relative prompts/ or prompt/
    p = BASE_DIR / "prompts" / "email_todo_extract.txt"
    if p.exists():
        return p

    p2 = BASE_DIR / "prompt" / "email_todo_extract.txt"
    if p2.exists():
        return p2

    # 3. frozen bundle (PyInstaller one-dir/onefile) may extract datas to _internal
    if getattr(sys, "frozen", False):
        # sys._MEIPASS for onefile; for one-dir, resources are relative to executable
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate = Path(meipass) / "_internal" / "prompt" / "email_todo_extract.txt"
            if candidate.exists():
                return candidate

        # also try next to executable
        exe_parent = Path(sys.executable).resolve().parent
        candidate2 = exe_parent / "_internal" / "prompt" / "email_todo_extract.txt"
        if candidate2.exists():
            return candidate2

    # 4. current working directory
    cwd_candidate = Path.cwd() / "prompts" / "email_todo_extract.txt"
    if cwd_candidate.exists():
        return cwd_candidate

    # not found
    return p


PROMPT_PATH = _resolve_prompt_path()


def load_system_prompt():
    if not PROMPT_PATH or not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {PROMPT_PATH}")

    return PROMPT_PATH.read_text(encoding="utf-8")


def truncate_text(text, max_length=5000):
    if not text:
        return ""

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    return text[:max_length] + "\n\n[正文过长，已截断]"


def build_email_prompt(mail):
    body = truncate_text(mail.get("body", ""))

    return f"""
请分析下面这一封邮件。

邮件ID: {mail.get("uid", "")}
发件人: {mail.get("from", "")}
收件人: {mail.get("to", "")}
抄送人: {mail.get("cc", "")}
主题: {mail.get("subject", "")}
时间: {mail.get("date", "")}

正文:
{body}
"""


def normalize_priority(priority):
    allowed = {"urgent", "high", "normal", "low"}

    if priority in allowed:
        return priority

    return "normal"


def build_source_mail_snapshot(mail, summary_text=""):
    return {
        "uid": str(mail.get("uid", "")),
        "subject": mail.get("subject", ""),
        "from": mail.get("from", ""),
        "to": mail.get("to", ""),
        "cc": mail.get("cc", ""),
        "date": mail.get("date", ""),
        "delivery_type": mail.get("delivery_type", "other"),
        "summary": summary_text,
        "body": mail.get("body", "")
    }


def normalize_single_email_result(result, mail):
    if not isinstance(result, dict):
        result = {}

    raw_summary = result.get("mail_summary", {})

    if not isinstance(raw_summary, dict):
        raw_summary = {}

    raw_todos = result.get("todos", [])

    if not isinstance(raw_todos, list):
        raw_todos = []

    summary_text = str(raw_summary.get("summary", "")).strip()

    if not summary_text:
        summary_text = f"邮件《{mail.get('subject', '')}》暂无摘要。"

    source_mail = build_source_mail_snapshot(
        mail,
        summary_text=summary_text
    )

    normalized_todos = []

    for todo in raw_todos:
        if not isinstance(todo, dict):
            continue

        title = str(todo.get("title", "")).strip()

        if not title:
            continue

        normalized_todos.append({
            "title": title,
            "priority": normalize_priority(todo.get("priority", "normal")),
            "deadline": todo.get("deadline"),
            "source_email_id": str(mail.get("uid", "")),
            "source_subject": mail.get("subject", ""),
            "source_from": mail.get("from", ""),
            "source_date": mail.get("date", ""),
            "source_delivery_type": mail.get("delivery_type", "other"),
            "source_mail": source_mail,
            "reason": str(todo.get("reason", "")).strip(),
            "status": "open",
            "is_manual": False
        })

    mail_summary = {
        "uid": str(mail.get("uid", "")),
        "subject": mail.get("subject", ""),
        "from": mail.get("from", ""),
        "to": mail.get("to", ""),
        "cc": mail.get("cc", ""),
        "date": mail.get("date", ""),
        "summary": summary_text,
        "has_todo": len(normalized_todos) > 0,
        "importance": normalize_priority(raw_summary.get("importance", "normal")),
        "delivery_type": mail.get("delivery_type", "other"),
        "body": mail.get("body", "")
    }

    return {
        "mail_summary": mail_summary,
        "todos": normalized_todos
    }


def extract_todos_from_single_email(mail):
    messages = [
        {
            "role": "system",
            "content": load_system_prompt()
        },
        {
            "role": "user",
            "content": build_email_prompt(mail)
        }
    ]

    result = call_llm_json(messages)

    return normalize_single_email_result(result, mail)


def deduplicate_todos(todos):
    seen = set()
    result = []

    for todo in todos:
        key = (
            todo.get("title", "").strip(),
            todo.get("deadline"),
            todo.get("source_email_id")
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(todo)

    return result


def sort_by_priority(items, priority_key="priority"):
    priority_order = {
        "urgent": 0,
        "high": 1,
        "normal": 2,
        "low": 3
    }

    return sorted(
        items,
        key=lambda x: (
            priority_order.get(x.get(priority_key, "normal"), 2),
            x.get("deadline") or "9999-12-31 23:59",
            x.get("source_date") or x.get("date") or ""
        )
    )


def extract_todos_from_emails(emails, on_progress=None, stop_check=None):
    if not emails:
        return {
            "summary": "本时间段内没有读取到邮件。",
            "mail_count": 0,
            "todo_count": 0,
            "mail_summaries": [],
            "todos": []
        }

    all_todos = []
    mail_summaries = []

    total = len(emails)

    for index, mail in enumerate(emails, start=1):
        if stop_check and stop_check():
            break

        uid = mail.get("uid", "")
        subject = mail.get("subject", "")

        print(f"[{index}/{total}] 正在分析邮件 UID={uid} 主题={subject}")

        if on_progress:
            on_progress(index, total)

        try:
            result = extract_todos_from_single_email(mail)

            mail_summaries.append(result["mail_summary"])
            all_todos.extend(result["todos"])

        except Exception as e:
            print(f"邮件 UID={uid} 提取失败: {e}")

            mail_summaries.append({
                "uid": str(uid),
                "subject": subject,
                "from": mail.get("from", ""),
                "to": mail.get("to", ""),
                "cc": mail.get("cc", ""),
                "date": mail.get("date", ""),
                "summary": f"该邮件分析失败：{e}",
                "has_todo": False,
                "importance": "normal",
                "delivery_type": mail.get("delivery_type", "other"),
                "body": mail.get("body", "")
            })

    cancelled = stop_check and stop_check()

    deduped_todos = deduplicate_todos(all_todos)
    sorted_todos = sort_by_priority(deduped_todos, priority_key="priority")
    sorted_mail_summaries = sort_by_priority(mail_summaries, priority_key="importance")

    if cancelled:
        summary = (
            f"分析已取消，已处理 {len(mail_summaries)}/{total} 封邮件，"
            f"生成 {len(sorted_todos)} 个待办。"
        )
    else:
        summary = (
            f"本时间段共读取 {total} 封邮件，"
            f"生成 {len(sorted_todos)} 个待办。"
        )

    return {
        "summary": summary,
        "mail_count": total,
        "todo_count": len(sorted_todos),
        "mail_summaries": sorted_mail_summaries,
        "todos": sorted_todos,
        "cancelled": cancelled,
    }