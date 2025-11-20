#!/bin/bash
# restart.sh - 重启 MCP 服务器

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在重启 MCP 服务器..."
echo "=================="

# 检查 stop.sh 是否存在
if [ ! -f "$SCRIPT_DIR/stop.sh" ]; then
    echo "错误: $SCRIPT_DIR/stop.sh 文件不存在"
    exit 1
fi

# 检查 startup.sh 是否存在
if [ ! -f "$SCRIPT_DIR/startup.sh" ]; then
    echo "错误: $SCRIPT_DIR/startup.sh 文件不存在"
    exit 1
fi

# 第一步：停止服务
echo "第一步：停止 MCP 服务器..."
"$SCRIPT_DIR/stop.sh"
STOP_RESULT=$?

if [ $STOP_RESULT -ne 0 ]; then
    echo "警告: 停止服务时遇到问题，继续重启流程..."
fi

# 等待一小段时间确保服务完全停止
echo "等待服务完全停止..."
sleep 3

# 第二步：启动服务
echo "第二步：启动 MCP 服务器..."
"$SCRIPT_DIR/startup.sh"
START_RESULT=$?

if [ $START_RESULT -eq 0 ]; then
    echo ""
    echo "✅ MCP 服务器重启成功"
    echo "=================="

    # 显示状态
    if [ -f "$SCRIPT_DIR/status.sh" ]; then
        echo ""
        echo "当前服务状态:"
        "$SCRIPT_DIR/status.sh"
    fi
else
    echo ""
    echo "❌ MCP 服务器重启失败"
    echo "=================="
    echo "请检查日志文件: $SCRIPT_DIR/mcp-server.log"
    exit 1
fi