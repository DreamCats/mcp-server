#!/bin/bash

# SuperTime MCP 服务安装脚本

echo "🚀 开始安装 SuperTime MCP 服务依赖..."

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ 已激活虚拟环境"
else
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 安装项目依赖
echo "📦 安装项目依赖..."
uv pip install -e .

# 安装开发依赖
echo "📦 安装开发依赖..."
uv pip install -e ".[dev]"

echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  启动服务: python start.py"
echo "  运行测试: pytest tests/ -v"
echo ""