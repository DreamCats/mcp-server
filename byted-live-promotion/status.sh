#!/bin/bash
# status.sh - 检查 MCP 服务器状态

echo "MCP 服务器状态检查"
echo "=================="

# 检查 pid 文件是否存在
if [ ! -f "mcp-server.pid" ]; then
    echo "状态: ❌ 未运行（找不到 pid 文件）"
    exit 0
fi

# 读取进程 ID
PID=$(cat mcp-server.pid)

# 检查进程是否存在
if ! kill -0 $PID 2>/dev/null; then
    echo "状态: ❌ 未运行（进程不存在）"
    echo "建议: 运行 ./stop.sh 清理状态"
    exit 0
fi

# 进程存在，获取详细信息
echo "状态: ✅ 运行中"
echo "进程 ID: $PID"
echo "端口: ${MCP_PORT:-8200}"
echo "环境变量 CAS_SESSION: $([ -n "$CAS_SESSION" ] && echo "已设置" || echo "未设置")"

# 检查日志文件
if [ -f "mcp-server.log" ]; then
    LOG_SIZE=$(stat -f%z "mcp-server.log" 2>/dev/null || stat -c%s "mcp-server.log" 2>/dev/null || echo "0")
    echo "日志文件: mcp-server.log (${LOG_SIZE} 字节)"

    # 显示最后几行日志
    echo ""
    echo "最近日志:"
    echo "----------"
    tail -n 5 mcp-server.log
else
    echo "日志文件: 不存在"
fi

# 检查端口监听
if command -v netstat >/dev/null 2>&1; then
    PORT_STATUS=$(netstat -an 2>/dev/null | grep -q ":${MCP_PORT:-8200} " && echo "✅" || echo "❌")
    echo "端口监听: ${PORT_STATUS} ${MCP_PORT:-8200}"
elif command -v lsof >/dev/null 2>&1; then
    PORT_STATUS=$(lsof -i :${MCP_PORT:-8200} >/dev/null 2>&1 && echo "✅" || echo "❌")
    echo "端口监听: ${PORT_STATUS} ${MCP_PORT:-8200}"
else
    echo "端口监听: 无法检测（缺少 netstat/lsof）"
fi

echo ""
echo "常用命令:"
echo "  查看完整日志: tail -f mcp-server.log"
echo "  停止服务器: ./stop.sh"
echo "  重启服务器: ./stop.sh && ./startup.sh"