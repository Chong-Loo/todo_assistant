from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys
from typing import Any

import keyring
import yaml

from app.db import DATA_DIR


BASE_DIR = Path(__file__).resolve().parent.parent
USER_CONFIG_PATH = DATA_DIR / "config.yaml"

MAIL_KEYRING_SERVICE = "todo_assistant"
LLM_KEYRING_SERVICE = "todo_assistant_llm"
LLM_TOKEN_ACCOUNT = "default"

def _default_config_path() -> Path:
    env_path = os.environ.get("TODO_ASSISTANT_CONFIG")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    candidates = [
        BASE_DIR / "config.yaml",
        Path.cwd() / "config.yaml",
    ]

    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).resolve().parent
        candidates.insert(0, exe_parent / "config.yaml")
        candidates.insert(1, exe_parent / "_internal" / "config.yaml")

    for path in candidates:
        if path.exists():
            return path

    return BASE_DIR / "config.yaml"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data if isinstance(data, dict) else {}


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)

    for key, value in override.items():
        if (
            isinstance(value, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value

    return result


MODEL_OPTIONS: list[str] = []


def load_default_config() -> dict[str, Any]:
    """只读取默认配置文件（忽略用户配置），用于获取内置默认值"""
    return _read_yaml(_default_config_path())


def load_config() -> dict[str, Any]:
    """
    读取应用配置。

    默认配置来自项目根目录 config.yaml；桌面设置页保存的用户配置
    位于 DATA_DIR/config.yaml，并覆盖默认配置中的同名字段。
    """
    return _merge_dict(
        _read_yaml(_default_config_path()),
        _read_yaml(USER_CONFIG_PATH),
    )


def load_user_config() -> dict[str, Any]:
    return _read_yaml(USER_CONFIG_PATH)


def save_user_config(config: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with USER_CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False,
        )


def update_user_config(section: str, values: dict[str, Any]) -> dict[str, Any]:
    config = load_user_config()
    current = config.get(section, {})

    if not isinstance(current, dict):
        current = {}

    current.update(values)
    config[section] = current
    save_user_config(config)

    return load_config()


def _llm_profile_key(model: str, endpoint: str) -> str:
    raw = f"{model.strip()}|{endpoint.strip()}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"profile-{digest}"


def list_llm_profiles() -> list[dict[str, Any]]:
    config = load_user_config()
    profiles = config.get("llm_profiles", [])

    if not isinstance(profiles, list):
        return []

    result = []
    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        model = str(profile.get("model", "")).strip()
        endpoint = str(profile.get("endpoint", "")).strip()
        token_account = str(profile.get("token_account", "")).strip()

        if model and endpoint:
            result.append({
                "model": model,
                "endpoint": endpoint,
                "token_account": token_account or _llm_profile_key(model, endpoint),
                "timeout": int(profile.get("timeout", 60) or 60),
            })

    return result


def save_llm_profile(
    model: str,
    endpoint: str,
    timeout: int = 60,
    token: str | None = None,
) -> dict[str, Any]:
    model = str(model or "").strip()
    endpoint = str(endpoint or "").strip()

    if not model:
        raise ValueError("模型名称不能为空")

    if not endpoint:
        raise ValueError("接口地址不能为空")

    token_account = _llm_profile_key(model, endpoint)

    if token:
        keyring.set_password(LLM_KEYRING_SERVICE, token_account, token)
        keyring.set_password(LLM_KEYRING_SERVICE, LLM_TOKEN_ACCOUNT, token)

    profile = {
        "model": model,
        "endpoint": endpoint,
        "timeout": int(timeout or 60),
        "token_account": token_account,
    }

    config = load_user_config()
    profiles = [
        item for item in list_llm_profiles()
        if item.get("token_account") != token_account
    ]
    profiles.insert(0, profile)
    config["llm_profiles"] = profiles
    config["llm"] = {
        "endpoint": endpoint,
        "model": model,
        "timeout": int(timeout or 60),
        "token_account": token_account,
    }
    save_user_config(config)

    return profile


def delete_llm_profile(token_account: str) -> bool:
    token_account = str(token_account or "").strip()
    if not token_account:
        return False

    config = load_user_config()
    profiles = [
        profile for profile in list_llm_profiles()
        if profile.get("token_account") != token_account
    ]
    config["llm_profiles"] = profiles

    current = config.get("llm", {})
    if isinstance(current, dict) and current.get("token_account") == token_account:
        if profiles:
            first = profiles[0]
            config["llm"] = {
                "endpoint": first.get("endpoint", ""),
                "model": first.get("model", ""),
                "timeout": int(first.get("timeout", 60) or 60),
                "token_account": first.get("token_account", ""),
            }
        else:
            config.pop("llm", None)

    try:
        keyring.delete_password(LLM_KEYRING_SERVICE, token_account)
    except Exception:
        pass

    save_user_config(config)
    return True


def get_llm_profile_token(token_account: str) -> str | None:
    token_account = str(token_account or "").strip()
    if not token_account:
        return None

    return keyring.get_password(LLM_KEYRING_SERVICE, token_account)


def get_mail_password(username: str) -> str | None:
    if not username:
        return None

    return keyring.get_password(MAIL_KEYRING_SERVICE, username)


def save_mail_password(username: str, password: str) -> None:
    if username and password:
        keyring.set_password(MAIL_KEYRING_SERVICE, username, password)


def get_llm_token() -> str | None:
    llm_cfg = load_config().get("llm", {})
    token_account = ""

    if isinstance(llm_cfg, dict):
        token_account = str(llm_cfg.get("token_account", "")).strip()

    if token_account:
        token = keyring.get_password(LLM_KEYRING_SERVICE, token_account)
        if token:
            return token

    return keyring.get_password(LLM_KEYRING_SERVICE, LLM_TOKEN_ACCOUNT)


def save_llm_token(token: str) -> None:
    if token:
        keyring.set_password(LLM_KEYRING_SERVICE, LLM_TOKEN_ACCOUNT, token)


THEME_PREF_KEY = "theme_preference"


def get_theme_preference() -> str | None:
    val = load_user_config().get(THEME_PREF_KEY)
    return str(val).strip() if val else None


def save_theme_preference(theme: str) -> None:
    config = load_user_config()
    config[THEME_PREF_KEY] = theme
    save_user_config(config)


def clean_app_stale_keys() -> None:
    """一次性迁移：删除 app 段中不再使用的旧键"""
    config = load_user_config()
    app = config.get("app", {})
    if not isinstance(app, dict):
        return
    app.pop("appearance", None)
    app.pop("confirm_close", None)
    app.pop("close_action", None)
    if not app:
        config.pop("app", None)
    else:
        config["app"] = app
    save_user_config(config)


def resolve_default_theme() -> str:
    """读取默认配置中的主题偏好"""
    return load_default_config().get("app", {}).get("appearance", {}).get("theme", "system")
