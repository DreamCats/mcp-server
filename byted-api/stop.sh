#!/bin/bash
# stop.sh - 停止 MCP 服务器

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在停止 MCP 服务器..."

# 检查 pid 文件是否存在
if [ ! -f "$SCRIPT_DIR/mcp-server.pid" ]; then
    echo "MCP 服务器未运行（找不到 pid 文件）"
    exit 0
fi

# 读取进程 ID
PID=$(cat "$SCRIPT_DIR/mcp-server.pid")

# 检查进程是否存在
if ! kill -0 $PID 2>/dev/null; then
    echo "MCP 服务器未运行（进程不存在）"
    rm -f "$SCRIPT_DIR/mcp-server.pid"
    exit 0
fi

# 尝试优雅停止
echo "正在停止进程 ID: $PID"
kill $PID

# 等待进程结束
for i in {1..10}; do
    if ! kill -0 $PID 2>/dev/null; then
        echo "✅ MCP 服务器已停止"
        rm -f "$SCRIPT_DIR/mcp-server.pid"
        exit 0
    fi
    echo -n "."
    sleep 1
done

# 如果优雅停止失败，强制终止
echo ""
echo "优雅停止失败，正在强制终止..."
kill -9 $PID 2>/dev/null

# 清理 pid 文件
rm -f "$SCRIPT_DIR/mcp-server.pid"

# 检查日志文件大小
if [ -f "$SCRIPT_DIR/mcp-server.log" ]; then
    LOG_SIZE=$(stat -f%z "$SCRIPT_DIR/mcp-server.log" 2>/dev/null || stat -c%s "$SCRIPT_DIR/mcp-server.log" 2>/dev/null || echo "0")
    if [ "$LOG_SIZE" -gt 10485760 ]; then  # 10MB
        echo "日志文件较大 (${LOG_SIZE} 字节)，建议清理"
    fi
fi

echo "✅ MCP 服务器已停止"
echo "日志文件保留: $SCRIPT_DIR/mcp-server.log"