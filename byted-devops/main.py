#!/usr/bin/env python3
"""
ByteDance MCP Server - Main Entry Point

This is the main entry point for the ByteDance MCP server that provides
service discovery capabilities with JWT authentication.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server import create_server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

def configure_logging(use_json=True):
    """配置日志格式

    Args:
        use_json: 是否使用JSON格式，True为JSON格式（简洁），False为控制台彩色格式
    """
    if use_json:
        # JSON格式 - 适合日志文件和生产环境
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()  # JSON格式，避免ANSI转义字符
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # 控制台彩色格式 - 适合开发环境
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer()  # 控制台彩色输出
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

logger = structlog.get_logger(__name__)


# 全局 MCP 服务器实例
mcp_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期管理"""
    global mcp_server

    # 启动 MCP 服务器
    logger.info("Starting ByteDance MCP Server")
    await mcp_server.start()

    logger.info("MCP Server initialized successfully")
    logger.info("Available tools:")
    logger.info("  - query_develope_task: Query develope task")

    yield

    # 清理资源
    logger.info("Stopping ByteDance MCP Server")
    await mcp_server.stop()


async def main():
    """Main entry point"""
    global mcp_server

    parser = argparse.ArgumentParser(description="ByteDance Bits Query MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8202")),
        help="Port to listen on (default: 8202)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--log-format",
        type=str,
        default=os.getenv("LOG_FORMAT", "json"),
        choices=["json", "console"],
        help="Log format: json (简洁格式) or console (彩色格式) (default: json)"
    )

    args = parser.parse_args()

    # Configure logging format
    configure_logging(use_json=(args.log_format == "json"))

    # Set log level
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))

    logger.info(
        "Starting ByteDance MCP Server",
        host=args.host,
        port=args.port,
        log_level=args.log_level
    )

    try:
        # 创建 MCP 服务器
        mcp_server = create_server()

        # 直接运行 MCP 的 ASGI 应用
        mcp_asgi_app = mcp_server.app.streamable_http_app()

        # Import uvicorn here to avoid import errors if not installed
        import uvicorn

        # Start the server
        logger.info(f"Starting MCP server on {args.host}:{args.port}")
        config = uvicorn.Config(
            mcp_asgi_app,  # 直接使用 MCP ASGI 应用
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower()
        )
        server = uvicorn.Server(config)
        await server.serve()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error("Server error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())