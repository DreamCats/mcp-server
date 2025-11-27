#!/bin/bash

# SuperTime MCP 服务状态检查脚本

# 配置变量
SERVICE_NAME="SuperTime MCP"
PORT=8201
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/supertime_mcp.pid"
LOG_FILE="$SCRIPT_DIR/supertime_mcp.log"

# 激活虚拟环境
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/../.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/../.venv/bin/activate"
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 ${SERVICE_NAME} 服务状态检查${NC}"
echo "=================================="

# 检查 PID 文件
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo -e "PID 文件: ${GREEN}存在${NC} (PID: $PID)"

    # 检查进程是否存在
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "进程状态: ${GREEN}运行中${NC}"

        # 获取进程信息
        if command -v ps > /dev/null; then
            echo "进程信息:"
            ps -p "$PID" -o pid,ppid,cmd,%mem,%cpu --no-headers 2>/dev/null | while read line; do
                echo "  $line"
            done
        fi

        # 检查端口
        if command -v lsof > /dev/null; then
            if lsof -i :$PORT -p "$PID" > /dev/null 2>&1; then
                echo -e "端口监听: ${GREEN}正常${NC} (端口: $PORT)"
            else
                echo -e "端口监听: ${RED}异常${NC} (端口: $PORT 未监听)"
            fi
        elif command -v netstat > /dev/null; then
            if netstat -tuln | grep ":$PORT " > /dev/null 2>&1; then
                echo -e "端口监听: ${GREEN}正常${NC} (端口: $PORT)"
            else
                echo -e "端口监听: ${RED}异常${NC} (端口: $PORT 未监听)"
            fi
        else
            echo -e "端口检查: ${YELLOW}跳过${NC} (未找到 lsof/netstat 命令)"
        fi

        # 检查内存使用
        if [ -f "/proc/$PID/status" ]; then
            MEMORY=$(grep VmRSS "/proc/$PID/status" | awk '{print $2 $3}')
            if [ -n "$MEMORY" ]; then
                echo "内存使用: $MEMORY"
            fi
        fi

        # 检查启动时间
        if [ -f "/proc/$PID/stat" ]; then
            START_TIME=$(ps -p "$PID" -o lstart --no-headers 2>/dev/null)
            if [ -n "$START_TIME" ]; then
                echo "启动时间: $START_TIME"
            fi
        fi

        # 检查日志文件
        if [ -f "$LOG_FILE" ]; then
            LOG_SIZE=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
            echo -e "日志文件: ${GREEN}存在${NC} (大小: $LOG_SIZE)"

            # 显示最近的几条日志
            echo "最近日志:"
            tail -n 5 "$LOG_FILE" | while read line; do
                echo "  $line"
            done
        else
            echo -e "日志文件: ${YELLOW}不存在${NC}"
        fi

        echo
        echo -e "${GREEN}✅ 服务运行正常${NC}"

    else
        echo -e "进程状态: ${RED}未运行${NC} (PID 文件存在但进程不存在)"
        echo -e "${YELLOW}🧹 清理 PID 文件...${NC}"
        rm -f "$PID_FILE"
        echo -e "${YELLOW}⚠️  服务状态异常，请重新启动${NC}"
    fi
else
    echo -e "PID 文件: ${RED}不存在${NC}"
    echo -e "进程状态: ${RED}未运行${NC}"
    echo -e "${YELLOW}⚠️  服务未启动${NC}"
fi

echo "=================================="

# 提供操作建议
if [ -f "$PID_FILE" ] && ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1; then
    echo
echo -e "${BLUE}可用操作:${NC}"
    echo "  ./stop.sh    - 停止服务"
    echo "  ./restart.sh - 重启服务"
    echo "  tail -f $LOG_FILE - 查看实时日志"
else
    echo
    echo -e "${BLUE}可用操作:${NC}"
    echo "  ./start.sh   - 启动服务"
fi