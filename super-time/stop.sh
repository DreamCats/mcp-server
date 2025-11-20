#!/bin/bash

# SuperTime MCP 服务停止脚本

set -e

# 配置变量
SERVICE_NAME="SuperTime MCP"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/supertime_mcp.pid"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🛑 停止 ${SERVICE_NAME} 服务...${NC}"

# 检查 PID 文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  未找到 PID 文件，服务可能未运行${NC}"
    exit 1
fi

# 读取 PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  服务进程不存在 (PID: $PID)${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

# 停止服务
echo -e "${GREEN}⏹️  正在停止服务 (PID: $PID)...${NC}"

# 尝试优雅停止
if kill -TERM "$PID" 2>/dev/null; then
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # 如果进程还在，强制停止
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  强制停止服务...${NC}"
        kill -KILL "$PID" 2>/dev/null || true
    fi

    # 删除 PID 文件
    rm -f "$PID_FILE"

    echo -e "${GREEN}✅ ${SERVICE_NAME} 服务已停止${NC}"
else
    echo -e "${RED}❌ 停止服务失败${NC}"
    exit 1
fi