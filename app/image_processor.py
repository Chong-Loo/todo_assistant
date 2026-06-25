import io
import base64
from pathlib import Path

from PIL import Image

from app.llm_client import call_llm_multimodal_json


BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_prompt_path() -> Path:
    p = BASE_DIR / "prompts" / "image_todo_extract.txt"
    return p


PROMPT_PATH = _resolve_prompt_path()


def load_system_prompt():
    if not PROMPT_PATH or not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def compress_image(image_bytes: bytes, max_size: int = 1280) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()


def encode_image_bytes(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def extract_todos_from_image(image_path: str):
    with open(image_path, "rb") as f:
        raw = f.read()
    compressed = compress_image(raw)
    b64 = encode_image_bytes(compressed)
    system_prompt = load_system_prompt()

    result = call_llm_multimodal_json(
        system_prompt=system_prompt,
        user_text="请分析这张图片，提取待办事项。",
        image_b64=b64
    )

    return normalize_image_result(result)


def normalize_image_result(result: dict) -> dict:
    if not isinstance(result, dict):
        return {"image_summary": "", "todos": []}

    raw_todos = result.get("todos", [])
    if not isinstance(raw_todos, list):
        raw_todos = []

    allowed = {"urgent", "high", "normal", "low"}
    normalized = []
    for todo in raw_todos:
        if not isinstance(todo, dict):
            continue
        title = str(todo.get("title", "")).strip()
        if not title:
            continue
        priority = todo.get("priority", "normal")
        if priority not in allowed:
            priority = "normal"
        normalized.append({
            "title": title,
            "priority": priority,
            "deadline": todo.get("deadline"),
            "content": str(todo.get("content", "")).strip(),
            "reason": str(todo.get("reason", "")).strip(),
        })

    return {
        "image_summary": str(result.get("image_summary", "")).strip(),
        "todos": normalized,
    }
