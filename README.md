# 智能待办助手

本项目是一个本地桌面端智能待办助手。

应用会读取企业邮箱邮件，调用大模型生成邮件摘要，并尽量从每封邮件中提取最多一个待办。待办支持状态、优先级、截止时间、附件、人工新增、完成、重新打开、删除等操作。


## 桌面客户端页面

- 今日概览：展示有效待办、未完成、紧急、逾期、高优先级等统计，并可点击待办跳转。
- 邮件待办：展示由邮件生成的未完成待办。
- 人工待办：展示人工新增的未完成待办。
- 已完成：展示已完成待办。
- 设置：维护邮箱配置、大模型配置和 keyring 凭据。

## 运行方式

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

如未安装 PyInstaller：

```powershell
pip install pyinstaller
```

### 2. 启动桌面客户端

```powershell
python client\app.py
```

### 3. 手动执行邮件分析任务

```powershell
python main.py
```

通常更推荐从桌面客户端顶部的“立即分析邮件”按钮触发，因为它会在后台线程执行并刷新界面。

## 配置与凭据

项目根目录的 `config.yaml` 是默认配置。桌面设置页保存的用户配置会写入用户数据目录中的 `config.yaml`，并覆盖默认配置中的同名项。

Windows 默认用户数据目录：

```text
%APPDATA%\todo_assistant
```

macOS 默认用户数据目录：

```text
~/Library/Application Support/todo_assistant
```

Linux 默认用户数据目录：

```text
~/.config/todo_assistant
```

可以通过环境变量覆盖数据目录：

```powershell
$env:TODO_ASSISTANT_DATA_DIR="D:\todo_assistant_data"
```

- 邮箱密码保存到系统 keyring，服务名为 `todo_assistant`。
- 大模型 Token 保存到系统 keyring，服务名为 `todo_assistant_llm`。
- 设置页保存大模型历史配置时，只在配置文件中保存模型名、接口 URL、timeout、token_account，不保存 Token 明文。

## macOS 打包说明

macOS `.app` 需要在 macOS 上打包，不能可靠地从 Windows 交叉打包。

建议单独维护 `todo_assistant_mac.spec`，并准备 `.icns` 图标。基本流程：

```bash
cd /path/to/todo_assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
python client/app.py
pyinstaller --clean todo_assistant_mac.spec
open dist/智能待办助手.app
```


## 开发注意事项

- 涉及待办数据的改动优先走 `app/todo_manager.py` 和 repository 层。
- 涉及配置和凭据的改动优先走 `app/settings.py`，不要直接把密码或 Token 写入配置文件。
- 打包后要重新验证 keyring、资源路径、prompt 路径和 SQLite 数据目录。

