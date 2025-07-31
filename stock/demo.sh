#!/bin/bash

# 股票 MCP 服务演示脚本
# Stock MCP Server Demo Script

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 股票 MCP 服务演示 ===${NC}"
echo ""

echo -e "${GREEN}1. 查看帮助信息${NC}"
echo "启动脚本帮助："
./start.sh --help
echo ""

echo "停止脚本帮助："
./stop.sh --help
echo ""

echo -e "${GREEN}2. 检查服务状态${NC}"
./stop.sh --status
echo ""

echo -e "${GREEN}3. 演示完成${NC}"
echo -e "${YELLOW}提示：${NC}"
echo "- 使用 './start.sh' 启动服务"
echo "- 使用 './start.sh -d' 后台启动服务"
echo "- 使用 './stop.sh' 停止服务"
echo "- 使用 './stop.sh -s' 查看服务状态"
echo "- 查看 USAGE.md 了解详细使用方法"
