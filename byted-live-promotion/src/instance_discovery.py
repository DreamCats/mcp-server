"""
Instance Address Discovery Module for ByteDance MCP Server

This module handles instance address discovery queries for TikTok ROW environments.
"""

from typing import Dict, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class InstanceDiscovery:
    """Instance Address Discovery with JWT authentication"""

    def __init__(self, jwt_manager):
        """
        Initialize Instance Discovery

        Args:
            jwt_manager: JWTAuthManager instance for authentication
        """
        self.jwt_manager = jwt_manager
        self.discovery_url = "https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/addrs"

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    async def discover_instances(self, psm: str, zone: str, idc: str,
                               cluster: Optional[str] = None) -> Dict[str, Any]:
        """
        Discover instance addresses for a given PSM with required zone and idc filters

        Args:
            psm: PSM identifier to search for (required)
            zone: Zone filter (required, e.g., "MVAALI", "SGALI")
            idc: IDC filter (required, e.g., "maliva", "my", "sg1")
            cluster: Cluster filter (optional, defaults to "default" if not provided)

        Returns:
            Instance address information for the specified PSM

        Raises:
            RuntimeError: If instance discovery fails

        Note:
            zone and idc are required parameters based on API requirements. If cluster is not specified,
            it defaults to "default".
        """
        logger.info("Discovering instances", psm=psm, zone=zone, idc=idc, cluster=cluster)

        # Get JWT token
        jwt_token = await self.jwt_manager.get_jwt_token()

        # Prepare request
        headers = {"x-jwt-token": jwt_token}
        params = {
            "psm": psm,
            "env": "prod",
            "zone": zone,
            "idc": idc
        }

        # Add cluster parameter, default to "default" if not provided
        params["cluster"] = cluster if cluster is not None else "default"

        try:
            logger.debug("Querying instance discovery API", url=self.discovery_url, psm=psm, headers=headers, params=params)

            response = await self.client.get(self.discovery_url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Log response details for debugging
            # logger.debug("Instance discovery response",
            #             status_code=response.status_code,
            #             response_headers=dict(response.headers),
            #             response_data=data)

            # Format response
            result = {
                "psm": psm,
                "filters": {
                    "zone": zone,
                    "idc": idc,
                    "cluster": cluster
                },
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            instances_count = len(data.get("data", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("Instance discovery completed", psm=psm, instances_found=instances_count, status_code=response.status_code)
            return result

        except httpx.TimeoutException:
            logger.warning("Instance discovery timeout", psm=psm)
            raise RuntimeError(f"Timeout while discovering instances for PSM: {psm}")

        except httpx.HTTPError as e:
            logger.error("Instance discovery HTTP error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while discovering instances for PSM {psm}: {e}")

        except Exception as e:
            logger.error("Instance discovery unexpected error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while discovering instances for PSM {psm}: {e}")

    async def get_instance_details(self, psm: str, zone: str, idc: str,
                                 cluster: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed instance address information for a specific PSM

        Args:
            psm: PSM identifier (required)
            zone: Zone filter (required, e.g., "MVAALI", "SGALI")
            idc: IDC filter (required, e.g., "maliva", "my", "sg1")
            cluster: Cluster filter (optional, defaults to "default" if not provided)

        Returns:
            Detailed instance address information

        Note:
            zone and idc are required parameters based on API requirements. If cluster is not specified,
            it defaults to "default".
        """
        result = await self.discover_instances(psm, zone, idc, cluster)

        # Format detailed response
        data = result.get("data", {})

        # Debug logging to understand the data structure
        logger.debug("Formatting instance details", data_type=type(data), data_content=data)

        # Handle the actual API response structure
        if isinstance(data, dict) and "data" in data:
            instances = data.get("data", [])
        elif isinstance(data, list):
            instances = data
        else:
            instances = []

        logger.debug("Extracted instances", instances_count=len(instances))

        return {
            "psm": psm,
            "instances": instances,
            "environment": "prod",
            "filters": result.get("filters", {}),
            "timestamp": result.get("timestamp", "Unknown")
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if hasattr(self, 'client'):
                import asyncio
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.client.aclose())
        except Exception:
            pass