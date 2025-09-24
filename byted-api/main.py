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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server import create_server
import structlog

# Configure logging
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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ByteDance MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8123")),
        help="Port to listen on (default: 8123)"
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

    args = parser.parse_args()

    # Set log level
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))

    logger.info(
        "Starting ByteDance MCP Server",
        host=args.host,
        port=args.port,
        log_level=args.log_level
    )

    # Check required environment variable
    if not os.getenv("CAS_SESSION"):
        logger.error("CAS_SESSION environment variable is not set")
        logger.error("Please set it before starting the server:")
        logger.error("export CAS_SESSION=\"your_cookie_value\"")
        sys.exit(1)

    try:
        # Create and start server
        server = create_server()
        await server.start()

        logger.info("MCP Server initialized successfully")
        logger.info("Available tools:")
        logger.info("  - search_psm_service: Search PSM service information")
        logger.info("  - check_jwt_status: Check JWT token status")
        logger.info("  - list_available_regions: List available regions")
        logger.info("  - search_multiple_services: Search multiple services")
        logger.info("  - discover_clusters: Discover clusters for PSM")
        logger.info("  - discover_instances: Discover instance addresses")
        logger.info("  - simulate_rpc_request: Simulate RPC requests")
        logger.info("  - query_logs_by_logid: Query logs by logid for US-TTP region")

        # Import uvicorn here to avoid import errors if not installed
        import uvicorn

        # Start the server
        logger.info(f"Starting server on {args.host}:{args.port}")
        await uvicorn.Server(
            uvicorn.Config(
                server.app.streamable_http_app,
                host=args.host,
                port=args.port,
                log_level=args.log_level.lower()
            )
        ).serve()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error("Server error", error=str(e))
        sys.exit(1)
    finally:
        # Cleanup
        try:
            if 'server' in locals():
                await server.stop()
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))


if __name__ == "__main__":
    asyncio.run(main())
