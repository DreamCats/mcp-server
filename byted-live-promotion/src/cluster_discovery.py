"""
Cluster Discovery Module for ByteDance MCP Server

This module handles cluster discovery queries for TikTok ROW environments.
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class ClusterDiscovery:
    """Cluster Discovery with JWT authentication"""

    def __init__(self, jwt_manager):
        """
        Initialize Cluster Discovery

        Args:
            jwt_manager: JWTAuthManager instance for authentication
        """
        self.jwt_manager = jwt_manager
        self.discovery_url = "https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/plane/clusters"

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    async def discover_clusters(self, psm: str) -> Dict[str, Any]:
        """
        Discover clusters for a given PSM

        Args:
            psm: PSM identifier to search for

        Returns:
            Cluster information for the specified PSM

        Raises:
            RuntimeError: If cluster discovery fails
        """
        logger.info("Discovering clusters", psm=psm)

        # Get JWT token
        jwt_token = await self.jwt_manager.get_jwt_token()

        # Prepare request
        headers = {"x-jwt-token": jwt_token}
        params = {
            "psm": psm,
            "test_plane": "1",
            "env": "prod"
        }

        try:
            logger.debug("Querying cluster discovery API", url=self.discovery_url, psm=psm, headers=headers, params=params)

            response = await self.client.get(self.discovery_url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Log response details for debugging
            # logger.debug("Cluster discovery response",
            #             status_code=response.status_code,
            #             response_headers=dict(response.headers),
            #             response_data=data)

            # Format response
            result = {
                "psm": psm,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            clusters_count = len(data.get("data", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("Cluster discovery completed", psm=psm, clusters_found=clusters_count, status_code=response.status_code)
            return result

        except httpx.TimeoutException:
            logger.warning("Cluster discovery timeout", psm=psm)
            raise RuntimeError(f"Timeout while discovering clusters for PSM: {psm}")

        except httpx.HTTPError as e:
            logger.error("Cluster discovery HTTP error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while discovering clusters for PSM {psm}: {e}")

        except Exception as e:
            logger.error("Cluster discovery unexpected error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while discovering clusters for PSM {psm}: {e}")

    async def get_cluster_details(self, psm: str) -> Dict[str, Any]:
        """
        Get detailed cluster information for a specific PSM

        Args:
            psm: PSM identifier

        Returns:
            Detailed cluster information
        """
        result = await self.discover_clusters(psm)

        # Format detailed response
        data = result.get("data", {})

        # Debug logging to understand the data structure
        logger.debug("Formatting cluster details", data_type=type(data), data_content=data)

        # Handle the actual API response structure
        if isinstance(data, dict) and "data" in data:
            clusters = data.get("data", [])
            # Try to extract region from clusters data
            if clusters and len(clusters) > 0:
                # Get region from first cluster's zone
                first_cluster = clusters[0]
                region = first_cluster.get("zone_display_name", "Unknown")
            else:
                region = "Unknown"
        elif isinstance(data, list):
            clusters = data
            # Get region from first cluster's zone
            if clusters and len(clusters) > 0:
                first_cluster = clusters[0]
                region = first_cluster.get("zone_display_name", "Unknown")
            else:
                region = "Unknown"
        else:
            clusters = []
            region = "Unknown"

        logger.debug("Extracted clusters", clusters_count=len(clusters), region=region)

        return {
            "psm": psm,
            "clusters": clusters,
            "region": region,
            "environment": "prod",
            "test_plane": "1",
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