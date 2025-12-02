#!/bin/bash
# startup.sh - 后台启动 MCP 服务器

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查虚拟环境是否存在
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "错误: 虚拟环境 $SCRIPT_DIR/.venv 不存在"
    echo "请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source "$SCRIPT_DIR/.venv/bin/activate"

# 检查 main.py 是否存在
if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo "错误: $SCRIPT_DIR/main.py 文件不存在"
    exit 1
fi

# 检查是否已在运行
if [ -f "$SCRIPT_DIR/mcp-server.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/mcp-server.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "MCP 服务器已在运行，进程 ID: $PID"
        echo "端口: ${MCP_PORT:-8202}"
        exit 0
    else
        echo "清理无效的 pid 文件"
        rm -f "$SCRIPT_DIR/mcp-server.pid"
    fi
fi

# 启动 MCP 服务器（后台模式）
echo "正在启动 MCP 服务器..."
echo "端口: ${MCP_PORT:-8202}"
echo "日志文件: $SCRIPT_DIR/mcp-server.log"

cd "$SCRIPT_DIR"
nohup python main.py --port ${MCP_PORT:-8202} > "$SCRIPT_DIR/mcp-server.log" 2>&1 &

# 保存进程 ID
echo $! > "$SCRIPT_DIR/mcp-server.pid"

# 等待启动
sleep 2

# 检查是否成功启动
PID=$(cat "$SCRIPT_DIR/mcp-server.pid")
if kill -0 $PID 2>/dev/null; then
    echo "✅ MCP 服务器启动成功"
    echo "进程 ID: $PID"
    echo "端口: ${MCP_PORT:-8202}"
    echo "日志: tail -f $SCRIPT_DIR/mcp-server.log"
else
    echo "❌ MCP 服务器启动失败"
    echo "请检查日志文件: $SCRIPT_DIR/mcp-server.log"
    rm -f "$SCRIPT_DIR/mcp-server.pid"
    exit 1
fi