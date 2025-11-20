#!/usr/bin/env python3
"""
SuperTime MCP 服务启动脚本
支持 streamable HTTP 协议
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from super_time import mcp


def main():
    """启动MCP服务"""
    print("🚀 启动 SuperTime MCP 服务...")
    print("📡 提供灵活的时间获取功能")
    print()

    # 配置HTTP协议参数
    transport = "streamable-http"  # 使用流式HTTP协议
    host = "0.0.0.0"  # 监听所有网络接口
    port = 8201  # 自定义端口

    print(f"🌐 使用 {transport} 协议")
    print(f"🔗 监听地址: http://{host}:{port}")
    print()

    # 运行MCP服务（使用HTTP协议）
    mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")