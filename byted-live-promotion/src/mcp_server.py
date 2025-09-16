"""
MCP Server Implementation for ByteDance Service Discovery

This module implements the MCP server with tools for JWT authentication and PSM service discovery.
"""

import os
import asyncio
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import structlog

try:
    from auth import JWTAuthManager
    from service_discovery import PSMServiceDiscovery
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from auth import JWTAuthManager
    from service_discovery import PSMServiceDiscovery

# Configure structured logging
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ByteDanceMCPServer:
    """ByteDance MCP Server with service discovery tools"""

    def __init__(self):
        """Initialize MCP server with tools"""
        self.mcp = FastMCP(
            name="byted-live-promotion",
            json_response=False,
            stateless_http=False
        )

        # Initialize components
        self.auth_manager = JWTAuthManager()
        self.service_discovery = PSMServiceDiscovery(self.auth_manager)

        # Register MCP tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def search_psm_service(keyword: str) -> str:
            """
            Search PSM service information with concurrent region queries

            Args:
                keyword: Service keyword to search for (e.g., oec.affiliate.monitor)

            Returns:
                Formatted service information including PSM, description, owners, etc.
            """
            try:
                logger.info("Searching PSM service", keyword=keyword)
                result = await self.service_discovery.get_service_details(keyword)

                if "error" in result:
                    return f"❌ Error: {result['error']}"

                # Format the response
                service = result
                response = f"""
🔍 **Service Found** ({result['match_type']} match)

📍 **Region**: {service['region']}
🔧 **PSM**: {service['psm']}
📝 **Description**: {service['description']}
👥 **Owners**: {service['owners']}
🏗️ **Framework**: {service['framework']}
🚀 **Platform**: {service['deployment_platform']}
📊 **Level**: {service['level']}
🔄 **Last Updated**: {service['last_updated']}
"""
                return response.strip()

            except Exception as e:
                logger.error("Error searching PSM service", keyword=keyword, error=str(e))
                return f"❌ Error searching service: {str(e)}"

        @self.mcp.tool()
        async def check_jwt_status() -> str:
            """
            Check JWT token status and validity

            Returns:
                JWT token status information including validity and expiration
            """
            try:
                logger.info("Checking JWT status")

                # Check if token exists and is valid
                if self.auth_manager.is_token_valid():
                    expires_in = self.auth_manager.expires_at - asyncio.get_event_loop().time()
                    minutes_left = expires_in / 60

                    return f"""
✅ **JWT Token Status: Valid**

⏰ **Expires in**: {minutes_left:.1f} minutes
🔑 **Token present**: Yes
🔄 **Auto-refresh**: Enabled
""".strip()
                else:
                    # Try to get new token
                    try:
                        await self.auth_manager.get_jwt_token()
                        return """
✅ **JWT Token Status: Refreshed**

🔄 **New token acquired**: Successfully
⏰ **Valid for**: ~60 minutes
🔑 **Ready for use**: Yes
""".strip()
                    except Exception as e:
                        return f"""
❌ **JWT Token Status: Invalid**

🚨 **Error**: {str(e)}
🔧 **Action needed**: Check CAS_SESSION environment variable
""".strip()

            except Exception as e:
                logger.error("Error checking JWT status", error=str(e))
                return f"❌ Error checking JWT status: {str(e)}"

        # @self.mcp.tool()
        async def list_available_regions() -> str:
            """
            List available regions for service discovery

            Returns:
                List of configured regions and their status
            """
            try:
                regions = self.service_discovery.regions
                response = "🌍 **Available Regions**:\n\n"

                for i, region in enumerate(regions, 1):
                    response += f"{i}. **{region}**\n"

                response += f"\n📊 **Total regions**: {len(regions)}"
                response += "\n🔄 **Query mode**: Concurrent (all regions)"

                return response.strip()

            except Exception as e:
                logger.error("Error listing regions", error=str(e))
                return f"❌ Error listing regions: {str(e)}"

        @self.mcp.tool()
        async def search_multiple_services(keywords: str) -> str:
            """
            Search multiple PSM services (comma-separated)

            Args:
                keywords: Comma-separated list of service keywords

            Returns:
                Results for all services
            """
            try:
                keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

                if not keyword_list:
                    return "❌ Please provide at least one service keyword"

                logger.info("Searching multiple services", keywords=keyword_list)

                # Search all services concurrently
                tasks = []
                for keyword in keyword_list:
                    task = self.service_discovery.get_service_details(keyword)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Format results
                response = f"🔍 **Search Results for {len(keyword_list)} Services**:\n\n"

                for i, (keyword, result) in enumerate(zip(keyword_list, results)):
                    if isinstance(result, Exception):
                        response += f"{i+1}. **{keyword}** ❌ Error: {str(result)}\n\n"
                    elif "error" in result:
                        response += f"{i+1}. **{keyword}** ❌ {result['error']}\n\n"
                    else:
                        service = result
                        response += f"{i+1}. **{keyword}** ✅ Found\n"
                        response += f"   📍 Region: {service['region']}\n"
                        response += f"   👥 Owners: {service['owners']}\n"
                        response += f"   🏗️ Framework: {service['framework']}\n\n"

                return response.strip()

            except Exception as e:
                logger.error("Error searching multiple services", error=str(e))
                return f"❌ Error searching services: {str(e)}"

    async def start(self):
        """Start the MCP server"""
        logger.info("Starting ByteDance MCP Server")

        # Test authentication on startup
        try:
            await self.auth_manager.get_jwt_token()
            logger.info("JWT authentication test successful")
        except Exception as e:
            logger.warning("JWT authentication test failed", error=str(e))
            logger.warning("Server will still start but authentication may fail")

    async def stop(self):
        """Stop the MCP server and cleanup resources"""
        logger.info("Stopping ByteDance MCP Server")

        # Cleanup resources
        try:
            await self.auth_manager.close()
            await self.service_discovery.close()
            logger.info("Resources cleaned up successfully")
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))

    @property
    def app(self):
        """Get the MCP app for uvicorn"""
        return self.mcp


def create_server() -> ByteDanceMCPServer:
    """Factory function to create MCP server"""
    return ByteDanceMCPServer()