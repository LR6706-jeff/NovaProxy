# NovaProxy (Python Pro Version)

这是一个为 Claude Code 优化的跨平台高级代理工具，基于 Python FastAPI 开发。

## ✨ 核心特性

- **可视化仪表盘**：通过浏览器访问 `http://localhost:3001` 直观管理代理状态。
- **智能模型路由**：自动将 Claude 模型名映射到 NVIDIA 性能最优的后端（如 GLM-4）。
- **多 Key 轮询**：支持配置多个 API Key，自动轮询，无惧限流。
- **零配置启动**：支持打包为 exe，双击即用，自动打开浏览器。
- **流式响应优化**：极致流畅的 AI 工具调用（Tool Use）和消息传输。

## 🚀 快速开始

### 方式 A：使用预编译可执行文件
1. 进入 `dist` 目录。
2. 双击运行 `NovaProxy.exe`。
3. 浏览器将自动打开管理面板。
4. 在面板中填入您的 NVIDIA API Key。

### 方式 B：从源码运行
```bash
cd python_proxy
pip install -r requirements.txt
python app.py
```

## 🛠️ 连接 Claude Code

在终端中设置环境变量：

```powershell
# Windows PowerShell
$env:ANTHROPIC_BASE_URL="http://localhost:3001"
$env:ANTHROPIC_API_KEY="anything"
claude
```

## 📂 项目结构
- `app.py`: 主程序
- `config.json`: 配置文件
- `templates/`: UI 模板
- `translator.py`: 协议转换逻辑
