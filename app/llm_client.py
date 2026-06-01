import os
import re
import json
from pathlib import Path

import requests

from app.settings import get_llm_token, load_config


BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_config_path() -> Path:
    # 1. explicit env var
    env_path = os.environ.get("TODO_ASSISTANT_CONFIG")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # 2. package relative config
    p = BASE_DIR / "config.yaml"
    if p.exists():
        return p

    # 3. working directory fallback
    p = Path.cwd() / "config.yaml"
    if p.exists():
        return p

    raise FileNotFoundError(
        "未找到 config.yaml。请将配置文件放在应用目录或通过环境变量 TODO_ASSISTANT_CONFIG 指定路径。"
    )


def clean_model_output(text: str) -> str:

    if not text:
        return ""

    # 删除 think
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.S
    )

    # 删除 markdown json fence
    text = text.replace("```json", "")
    text = text.replace("```", "")

    return text.strip()


def call_llm(messages):

    config = load_config()

    llm_cfg = config["llm"]

    token = get_llm_token()

    if not token:
        raise RuntimeError("没有读取到 LLM Token")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": llm_cfg["model"],
        "messages": messages,
        "temperature": 0.1,
        "stream": False
    }

    response = requests.post(
        llm_cfg["endpoint"],
        headers=headers,
        json=payload,
        timeout=llm_cfg.get("timeout", 60)
    )

    response.raise_for_status()

    data = response.json()

    content = data["choices"][0]["message"]["content"]

    return clean_model_output(content)


def call_llm_json(messages):

    result = call_llm(messages)

    try:

        return json.loads(result)

    except Exception as e:

        print("\n===== 非法JSON =====\n")
        print(result)

        raise RuntimeError(
            "模型输出不是合法JSON"
        ) from e
