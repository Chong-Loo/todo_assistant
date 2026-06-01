"""
手动设置密码的脚本
"""

import keyring

# LLM Token
keyring.set_password(
    "todo_assistant_llm",
    "default",
    ""
)
print("LLM Token 已保存")


# # 邮箱密码
# keyring.set_password(
#     "todo_assistant",
#     "default",
#     ""
# )

# print("密码已保存")