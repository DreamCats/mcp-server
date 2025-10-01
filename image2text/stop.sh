#!/bin/bash

# image2text MCP服务器停止脚本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止 image2text MCP 服务器 (PID: $PID)..."
        kill -TERM $PID

        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "服务器已成功停止"
                rm -f "$PID_FILE"
                exit 0
            fi
            sleep 1
        done

        # 如果进程还在，强制结束
        echo "强制停止服务器..."
        kill -KILL $PID
        rm -f "$PID_FILE"
        echo "服务器已强制停止"
    else
        echo "服务器进程不存在，可能已停止"
        rm -f "$PID_FILE"
    fi
else
    # 尝试通过端口查找进程
    PID=$(lsof -ti :8201)
    if [ -n "$PID" ]; then
        echo "停止占用端口 8201 的进程 (PID: $PID)..."
        kill -TERM $PID
        echo "进程已停止"
    else
        echo "没有找到运行中的服务器进程"
    fi
fi