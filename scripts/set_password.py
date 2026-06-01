import keyring

keyring.set_password(
    "todo_assistant_llm",
    "default",
    ""
)

print("LLM Token 已保存")