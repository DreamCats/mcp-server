#!/bin/bash

# SuperTime MCP 服务启动脚本
# 使用端口 8201

set -e

# 配置变量
SERVICE_NAME="SuperTime MCP"
PORT=8201
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/supertime_mcp.pid"
LOG_FILE="$SCRIPT_DIR/supertime_mcp.log"
PYTHON_CMD="python3"

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
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 启动 ${SERVICE_NAME} 服务...${NC}"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  ${SERVICE_NAME} 服务已在运行中 (PID: $PID)${NC}"
        echo -e "${YELLOW}   监听端口: $PORT${NC}"
        exit 1
    else
        # PID 文件存在但进程不在，删除旧 PID 文件
        rm -f "$PID_FILE"
    fi
fi

# 检查端口是否被占用
if lsof -i :$PORT > /dev/null 2>&1; then
    echo -e "${RED}❌ 端口 $PORT 已被占用${NC}"
    echo -e "${RED}   请检查其他服务或更换端口${NC}"
    exit 1
fi

# 检查 Python 环境
echo -e "${GREEN}📋 检查 Python 环境...${NC}"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装或未在 PATH 中${NC}"
    exit 1
fi

# 检查依赖
echo -e "${GREEN}📦 检查依赖...${NC}"
if ! $PYTHON_CMD -c "import fastmcp" 2>/dev/null; then
    echo -e "${RED}❌ fastmcp 依赖未安装${NC}"
    echo -e "${RED}   请运行: pip install fastmcp${NC}"
    exit 1
fi

# 启动服务
echo -e "${GREEN}▶️  启动服务中...${NC}"
echo -e "${GREEN}   协议: streamable-http${NC}"
echo -e "${GREEN}   端口: $PORT${NC}"
echo -e "${GREEN}   日志: $LOG_FILE${NC}"
echo

# 后台启动服务
nohup $PYTHON_CMD start.py > "$LOG_FILE" 2>&1 &
PID=$!

# 等待服务启动
sleep 3

# 检查服务是否成功启动
if ps -p "$PID" > /dev/null 2>&1; then
    echo "$PID" > "$PID_FILE"
    echo -e "${GREEN}✅ ${SERVICE_NAME} 服务启动成功!${NC}"
    echo -e "${GREEN}   PID: $PID${NC}"
    echo -e "${GREEN}   端口: $PORT${NC}"
    echo -e "${GREEN}   访问: http://localhost:$PORT${NC}"
    echo
    echo -e "${YELLOW}📋 查看日志: tail -f $LOG_FILE${NC}"
else
    echo -e "${RED}❌ ${SERVICE_NAME} 服务启动失败${NC}"
    echo -e "${RED}   请查看日志: $LOG_FILE${NC}"
    exit 1
fi