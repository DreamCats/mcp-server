#!/bin/bash

# SuperTime MCP 服务重启脚本

set -e

# 配置变量
SERVICE_NAME="SuperTime MCP"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

echo -e "${BLUE}🔄 ${SERVICE_NAME} 服务重启${NC}"
echo "=================================="

# 检查 stop.sh 是否存在
if [ ! -f "$SCRIPT_DIR/stop.sh" ]; then
    echo -e "${RED}❌ stop.sh 脚本不存在${NC}"
    exit 1
fi

# 检查 start.sh 是否存在
if [ ! -f "$SCRIPT_DIR/start.sh" ]; then
    echo -e "${RED}❌ start.sh 脚本不存在${NC}"
    exit 1
fi

# 第一步：停止服务
echo -e "${GREEN}第一步: 停止服务${NC}"
echo "----------------------------------"
if bash "$SCRIPT_DIR/stop.sh"; then
    echo -e "${GREEN}✅ 服务停止成功${NC}"
    echo
else
    echo -e "${YELLOW}⚠️  服务停止失败或不存在${NC}"
    echo
fi

# 等待一下确保端口释放
echo -e "${YELLOW}⏳ 等待端口释放...${NC}"
sleep 2

# 第二步：启动服务
echo -e "${GREEN}第二步: 启动服务${NC}"
echo "----------------------------------"
if bash "$SCRIPT_DIR/start.sh"; then
    echo
    echo -e "${GREEN}✅ 服务重启成功!${NC}"
    echo "=================================="

    # 显示状态
    echo
    echo -e "${BLUE}📊 服务状态:${NC}"
    bash "$SCRIPT_DIR/status.sh" | grep -E "(进程状态|端口监听|服务运行)" || true
else
    echo
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo "=================================="
    exit 1
fi