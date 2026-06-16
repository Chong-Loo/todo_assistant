"""
初始化默认模型 Token 到系统凭据（用于部署时执行一次）

用法：
  python scripts/set_password.py

在打包后首次部署时，IT 人员运行此脚本将 Token 写入系统 keyring，
用户打开客户端即可直接使用默认模型，无需手动输入 Token。
"""

import keyring

# ===== 修改为你的默认模型 Token =====
DEFAULT_TOKEN = "894e442a9b9ac05ce53bce168595105daab05c25"
# =================================

keyring.set_password(
    "todo_assistant_llm",
    "default",
    DEFAULT_TOKEN
)
print("✅ 默认模型 Token 已保存到系统凭据（keyring）")

# 同时保存为默认配置文件的 token_account
from pathlib import Path
import hashlib, yaml

# 读取默认配置获取 endpoint 和 model
candidates = [
    Path(__file__).resolve().parent.parent / "config.yaml",
    Path.cwd() / "config.yaml",
]
config_path = None
for c in candidates:
    if c.exists():
        config_path = c
        break

if config_path:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    llm = cfg.get("llm", {})
    model = str(llm.get("model", "")).strip()
    endpoint = str(llm.get("endpoint", "")).strip()
    if model and endpoint:
        raw = f"{model}|{endpoint}".encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()[:16]
        token_account = f"profile-{digest}"
        keyring.set_password("todo_assistant_llm", token_account, DEFAULT_TOKEN)
        print(f"✅ 同时保存到配置文件凭据（{token_account}）")


# # 邮箱密码（如需）
# keyring.set_password(
#     "todo_assistant",
#     "your_username",
#     "your_password"
# )
# print("邮箱密码已保存")