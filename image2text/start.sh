#!/bin/bash

# image2text MCP服务器启动脚本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 激活虚拟环境
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "警告: 未找到虚拟环境，使用系统Python"
fi

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$SCRIPT_DIR/src"

# 检查端口是否被占用
if lsof -i :8201 > /dev/null 2>&1; then
    echo "端口 8201 已被占用，请先运行 stop.sh 停止现有服务"
    exit 1
fi

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

# 启动服务器
echo "启动 image2text MCP 服务器..."
echo "端口: 8201"
echo "日志: logs/server.log"
echo ""

nohup python "$SCRIPT_DIR/src/main.py" \
    --port 8201 \
    --host 0.0.0.0 \
    --log-level INFO \
    > "$SCRIPT_DIR/logs/server.log" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$SCRIPT_DIR/logs/server.pid"

echo "服务器已启动，PID: $SERVER_PID"
echo "日志文件: $SCRIPT_DIR/logs/server.log"
echo ""
echo "使用以下命令停止服务器:"
echo "  ./stop.sh"
echo ""
echo "使用以下命令查看日志:"
echo "  tail -f logs/server.log"