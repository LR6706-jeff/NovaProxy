#!/bin/bash

echo "🚀 NovaProxy for Mac 正在启动..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null
then
    echo "❌ 错误: 未检测到 Python3，请先安装 Python (brew install python)"
    exit
fi

# 安装必要依赖
echo "📦 正在检查/安装必要组件..."
python3 -m pip install fastapi uvicorn httpx jinja2 pydantic -q

# 运行程序
echo "✨ 启动成功！请在浏览器访问 http://localhost:3001"
python3 app.py
