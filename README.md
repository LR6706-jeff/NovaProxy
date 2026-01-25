# 🌌 NovaProxy: The Elegant Claude-to-NVIDIA Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![UI: Minimalist](https://img.shields.io/badge/UI-Minimalist-brightgreen)](https://github.com/)

**NovaProxy** 是一款极简且优雅的代理转换工具，旨在弥合 Anthropic (Claude) 协议与 NVIDIA NIM (OpenAI 格式) 之间的鸿沟。它让你可以使用任何原生支持 Claude 的客户端（如 Claude Code, Cursor），无缝调用 NVIDIA 驱动的高性能模型。

[English](#features) | [简体中文](#核心特性)

---

## 核心特性
- 🎨 **晨曦审美界面**：内置“暖沙”风格极简 Web 后台，告别冰冷的命令行配置。
- 🚀 **开箱即用**：支持 Windows 单文件运行，启动后自动弹出浏览器管理后台。
- 🔄 **智能协议转换**：全自动处理复杂的 Anthropic 消息结构与 NVIDIA/OpenAI 流式响应转换。
- 🛡️ **安全第一**：配置本地化存储，支持设置私有访问验证密钥，保护您的额度不被盗用。
- ⚡ **高性能异步**：基于 Python FastAPI + Httpx 驱动，超低延迟响应。

## Features
- 🎨 **Minimalist UI**: Built-in "Warm Sand" aesthetic dashboard for effortless configuration.
- 🚀 **Instant-on**: Standalone EXE for Windows with auto-browser-opening functionality.
- 🔄 **Smart Protocol Translation**: Seamlessly converts Anthropic message blocks to NVIDIA NIM (OpenAI) format.
- 🛡️ **Privacy & Security**: Local config storage with optional access token for API protection.
- ⚡ **FastAPI Driven**: High-performance asynchronous IO with minimal overhead.

---

## 📽️ 界面演示 / Screenshots
*(建议在此处上传一张您刚才看到的暖沙色后台截图)*

---

## 🚀 快速上手 / Quick Start

### 1. 运行程序
下载发行版中的 `NovaProxy.exe` 并双击。

### 2. 后台设置
程序启动后会自动访问 [http://localhost:3001](http://localhost:3001)：
1.  输入您的 **NVIDIA API Key**。
2.  点击 **保存** 即可立即生效。

### 3. 连接客户端 (以 Claude Code 为例)
在您的终端中设置以下环境变量：

```powershell
# PowerShell
$env:ANTHROPIC_BASE_URL="http://localhost:3001/v1"
$env:ANTHROPIC_API_KEY="any_string"
claude
```

---

## 🛠️ 技术栈 / Tech Stack

- **Core**: Python 3.13 / FastAPI
- **Proxy**: Httpx (Streaming support)
- **UI**: Vanilla HTML / CSS (Grid & Flex)
- **Packaging**: PyInstaller

## 📄 协议 / License
本项目采用 [MIT License](LICENSE) 协议发布。

---
> **Disclaimer**: 本项目仅供学习研究使用，请确保在符合 NVIDIA 与 Anthropic API 使用条款的前提下运行。
