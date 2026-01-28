# ✨ NovaProxy (Pro Version)

> **优雅、极速且全能的 Claude API 代理工具** —— 专为 Claude Code 设计，完美桥接 Anthropic 协议与 NVIDIA NIM 平台。

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-blueviolet?style=for-the-badge)](https://github.com/LR6706-jeff/NovaProxy)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge)](https://www.python.org/)

---

## 🚀 核心亮点

*   **💎 绝美仪表盘**：内置基于现代毛玻璃 (Glassmorphism) 风格的可视化面板，实时监控请求流、Token 消耗及系统状态。
*   **⚡ 极致性能**：采用 FastAPI 异步架构，结合全局 HTTP 连接池与重试机制，告别连接抖动与高延迟。
*   **🤖 智能模型重定向**：支持模型映射字典，自动将 Claude 模型请求路由至 NVIDIA 平台最兼容的高性能模型（如 GLM-4, Minimax 等）。
*   **🔄 多 Key 轮询**：支持配置多个 NVIDIA API Key，通过负载均衡算法自动轮询，无惧单 Key 额度与频率限制。
*   **🔐 访问安全**：可选的 `Server API Key` 保护，防止公网部署时的盗刷风险，支持在 UI 界面一键开关。
*   **🍎 全平台覆盖**：提供 Windows 绿色单文件版 (.exe) 以及 Mac/Linux 自动化运行脚本。

---

## 📦 安装与运行

### **方式 1：Windows (推荐)**
1.  下载并双击运行 `NovaProxy_Portable.exe`。
2.  程序将自动在浏览器中打开 **控制中心** (`http://localhost:3001`)。
3.  在页面中填入您的 NVIDIA API Key 并保存。

### **方式 2：Mac / Linux**
1.  解压源码包，在终端进入该目录。
2.  赋予权限并运行启动脚本：
    ```bash
    chmod +x start.sh
    ./start.sh
    ```
3.  脚本会自动检查 Python 环境并安装所需依赖。

---

## 🔗 客户端接入指南

### **Claude Code 配置**
在您的终端环境变量中设置以下配置，即可让 `claude-code` 满血运行：

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_BASE_URL="http://127.0.0.1:3001"
$env:ANTHROPIC_API_KEY="your_password"  # 若未设置访问密码，此处可填任意内容
claude
```

**Mac / Linux:**
```bash
export ANTHROPIC_BASE_URL=http://localhost:3001
export ANTHROPIC_API_KEY=your_password
claude
```

---

## ⚙️ 配置文件说明 (`config.json`)

```json
{
  "nvidia_url": "https://integrate.api.nvidia.com/v1/chat/completions",
  "nvidia_keys": ["nvapi-xxx", "nvapi-yyy"],
  "model_mapping": {
    "claude-3-5-sonnet-latest": "z-ai/glm-4-9b-chat"
  },
  "default_model": "z-ai/glm-4-9b-chat",
  "server_api_key": null, 
  "port": 3001
}
```
*   `server_api_key`: 设置后客户端需通过 API Key 校验，设为 `null` 禁用校验。
*   `model_mapping`: 自定义模型转换规则。

---

## 🛠️ 技术栈

- **Backend**: FastAPI, Uvicorn, HTTPX
- **Frontend**: Vanilla JS, HTML5 (Glassmorphism UI)
- **Packaging**: PyInstaller

---

## 📜 开源协议
MIT License. 欢迎 Star 和参与贡献！
