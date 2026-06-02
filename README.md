# 智能待办助手

本项目是一个本地桌面端智能待办助手，使用 **PySide6 桌面客户端 + SQLite 本地持久化**。

应用读取企业邮箱邮件，调用大模型生成邮件摘要，并尽量从每封邮件中提取最多一个待办。待办支持状态、优先级、截止时间、附件、阶段完成情况、人工新增/编辑、完成、重新打开、删除等操作。

## 功能特性

- **邮件拉取**：支持增量拉取（仅拉取未处理邮件）和按天拉取（指定回溯天数）两种模式
- **大模型分析**：为每封邮件生成摘要，最多提取一个待办
- **待办管理**：状态（未完成/已完成/已取消/已暂缓）、优先级（紧急/高/普通/低）、截止时间、附件、备注
- **阶段完成情况**：每个待办可添加多个阶段子任务，支持复选框标记完成、截止时间、添加/删除
- **人工待办**：支持新增和编辑，可上传附件
- **主页概览**：统计方框（全部/逾期/紧急/高优先级/三天内截止），点击可查看筛选列表；待办清单支持排序（截止时间/优先级/创建时间/来源）
- **已完成搜索与删除**：已完成页面支持关键字搜索和删除待办
- **自动清理**：已完成待办最多保留 3 天或 30 条
- **安全存储**：邮箱密码和大模型 Token 保存在系统 keyring，配置文件不存储明文凭据

## 页面说明

- **主页**：统计方框 + 可排序未完成待办清单
- **邮件待办**：邮件生成的未完成待办
- **人工待办**：人工新增的未完成待办（支持编辑）
- **已完成**：已完成待办（支持搜索和删除）
- **设置**：邮箱 IMAP 配置、大模型接口地址/模型名/Token、keyring 凭据管理

## 快速启动

```powershell
pip install -r requirements.txt
python client\app.py
```

## 手动执行邮件分析

```powershell
python main.py
```

或在桌面客户端主页点击"立即分析邮件"按钮。

## 配置说明

默认配置在项目根目录 `aml`config.y。设置页保存的用户配置写入用户数据目录：

- Windows：`%APPDATA%\todo_assistant`
- macOS：`~/Library/Application Support/todo_assistant`
- Linux：`~/.config/todo_assistant`

可通过环境变量覆盖：`$env:TODO_ASSISTANT_DATA_DIR="D:\path"`

敏感信息（邮箱密码、大模型 Token）保存在系统 keyring，不写入配置文件。

## Windows exe 打包

```powershell
pip install pyinstaller
pyinstaller --clean todo_assistant.spec
```

输出位置：`dist\todo_assistant\todo_assistant.exe`
