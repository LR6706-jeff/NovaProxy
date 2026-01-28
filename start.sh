#!/bin/bash

# NovaProxy Mac 启动脚本
# 使用方法: chmod +x start.sh && ./start.sh

echo "✨ NovaProxy for Mac"
echo "===================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装: brew install python3"
    exit 1
fi

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查并安装依赖
if [ ! -f ".deps_installed" ]; then
    echo "📦 首次运行，正在安装依赖..."
    python3 -m pip install fastapi uvicorn httpx jinja2 pydantic --quiet
    touch .deps_installed
    echo "✅ 依赖安装完成"
fi

# 启动服务
echo "🚀 正在启动 NovaProxy..."
python3 app.py
