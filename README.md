# NovaProxy

将 Claude API 请求转发到 NVIDIA NIM 平台的代理工具。

## 🚀 快速开始

### Windows 用户
直接双击 `NovaProxy_Portable.exe` 即可运行。

### Mac/Linux 用户
```bash
chmod +x start.sh
./start.sh
```

## ⚙️ 配置

编辑 `config.json`：

```json
{
  "nvidia_url": "https://integrate.api.nvidia.com/v1/chat/completions",
  "nvidia_keys": ["你的 NVIDIA API Key"],
  "model_mapping": {},
  "default_model": "z-ai/glm4.7",
  "server_api_key": null,
  "port": 3001
}
```

- `nvidia_keys`: NVIDIA API Key，支持多个轮询
- `default_model`: 默认使用的模型
- `server_api_key`: 访问密码，设为 `null` 则不需要密码

## 🔗 连接 Claude Code

```bash
# Mac/Linux
export ANTHROPIC_BASE_URL=http://localhost:3001
export ANTHROPIC_API_KEY=anything
claude

# Windows PowerShell
$env:ANTHROPIC_BASE_URL="http://localhost:3001"
$env:ANTHROPIC_API_KEY="anything"
claude
```

## 📊 管理面板

启动后访问 http://localhost:3001 查看实时统计和修改配置。
