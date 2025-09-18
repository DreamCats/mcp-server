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
    from cluster_discovery import ClusterDiscovery
    from instance_discovery import InstanceDiscovery
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from auth import JWTAuthManager
    from service_discovery import PSMServiceDiscovery
    from cluster_discovery import ClusterDiscovery
    from instance_discovery import InstanceDiscovery

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
        self.cluster_discovery = ClusterDiscovery(self.auth_manager)
        self.instance_discovery = InstanceDiscovery(self.auth_manager)

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

        @self.mcp.tool()
        async def discover_clusters(psm: str) -> str:
            """
            Discover clusters for a given PSM in TikTok ROW environments

            Args:
                psm: PSM identifier to search for clusters (e.g., oec.affiliate.monitor)

            Returns:
                Cluster information for the specified PSM
            """
            try:
                logger.info("Discovering clusters", psm=psm)
                result = await self.cluster_discovery.get_cluster_details(psm)

                # Format the response
                clusters = result.get('clusters', [])

                if not clusters:
                    return f"❌ No clusters found for PSM: {psm}"

                response = f"""
📍 **Cluster Discovery Results**
🔧 **PSM**: {result['psm']}
🌍 **Region**: {result['region']}
🧪 **Test Plane**: {result['test_plane']}
🖥️ **Environment**: {result['environment']}

📊 **Clusters Found**: {len(clusters)}
"""

                # Add cluster details
                for i, cluster in enumerate(clusters[:5], 1):  # Limit to first 5 clusters
                    response += f"\n--- Cluster {i} ---\n"
                    for key, value in cluster.items():
                        response += f"  {key}: {value}\n"

                if len(clusters) > 5:
                    response += f"\n... and {len(clusters) - 5} more clusters\n"

                response += f"\n⏰ **Timestamp**: {result['timestamp']}"

                return response.strip()

            except Exception as e:
                logger.error("Error discovering clusters", psm=psm, error=str(e))
                return f"❌ Error discovering clusters for {psm}: {str(e)}"

        @self.mcp.tool()
        async def discover_instances(psm: str, zone: str, idc: str, cluster: str = None) -> str:
            """
            Discover instance addresses for a given PSM with required zone and idc filters

            Args:
                psm: PSM identifier to search for instances (e.g., oec.affiliate.monitor)
                zone: Zone filter (required, e.g., "MVAALI", "SGALI")
                idc: IDC filter (required, e.g., "maliva", "my", "sg1")
                cluster: Cluster filter (optional, defaults to "default" if not provided)

            Returns:
                Instance address information for the specified PSM

            Note:
                zone and idc are required parameters based on API requirements. If cluster is not specified,
                it defaults to "default".
            """
            try:
                logger.info("Discovering instances", psm=psm, zone=zone, idc=idc, cluster=cluster)
                result = await self.instance_discovery.get_instance_details(psm, zone, idc, cluster)

                # Format the response
                instances = result.get('instances', [])

                if not instances:
                    return f"❌ No instances found for PSM: {psm}"

                response = f"""
📍 **Instance Discovery Results**
🔧 **PSM**: {result['psm']}
🖥️ **Environment**: {result['environment']}

📊 **Instances Found**: {len(instances)}
"""

                # Add filter information if provided
                filters = result.get('filters', {})
                active_filters = {k: v for k, v in filters.items() if v is not None}
                if active_filters:
                    response += "\n🔍 **Active Filters**:\n"
                    for key, value in active_filters.items():
                        response += f"  {key}: {value}\n"

                # Add instance details (limit to first 5 instances)
                for i, instance in enumerate(instances[:5], 1):
                    response += f"\n--- Instance {i} ---\n"
                    if isinstance(instance, dict):
                        # Handle dictionary format
                        for key, value in instance.items():
                            response += f"  {key}: {value}\n"
                    elif isinstance(instance, str):
                        # Handle string format (IP:port addresses)
                        response += f"  Address: {instance}\n"
                    else:
                        # Handle other formats
                        response += f"  Instance: {instance}\n"

                if len(instances) > 5:
                    response += f"\n... and {len(instances) - 5} more instances\n"

                response += f"\n⏰ **Timestamp**: {result['timestamp']}"

                return response.strip()

            except Exception as e:
                logger.error("Error discovering instances", psm=psm, error=str(e))
                return f"❌ Error discovering instances for {psm}: {str(e)}"

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
            await self.cluster_discovery.close()
            await self.instance_discovery.close()
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