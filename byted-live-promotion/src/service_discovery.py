"""
PSM Service Discovery Module for ByteDance MCP Server

This module handles concurrent PSM service queries across multiple regions.
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class PSMServiceDiscovery:
    """PSM Service Discovery with concurrent region querying"""

    def __init__(self, jwt_manager):
        """
        Initialize PSM Service Discovery

        Args:
            jwt_manager: JWTAuthManager instance for authentication
        """
        self.jwt_manager = jwt_manager
        self.regions = [
            "https://ms-neptune.byted.org",
            "https://ms-neptune.tiktok-us.org"
        ]

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    async def search_service(self, keyword: str) -> Dict[str, Any]:
        """
        Search PSM service with concurrent region queries

        Args:
            keyword: Service keyword to search for

        Returns:
            Service information from the best matching region

        Raises:
            RuntimeError: If all regions fail
        """
        logger.info("Searching PSM service", keyword=keyword)

        # Get JWT token
        jwt_token = await self.jwt_manager.get_jwt_token()

        # Create concurrent tasks for all regions
        tasks = []
        for region in self.regions:
            task = self._search_single_region(region, keyword, jwt_token)
            tasks.append(task)

        # Execute concurrent requests
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Select best result
        best_result = self._select_best_result(results, keyword)

        if best_result:
            logger.info("Service found", region=best_result.get("region"), psm=keyword)
            return best_result
        else:
            logger.warning("No matching service found", keyword=keyword)
            return {"error": f"No matching service found for keyword: {keyword}"}

    async def _search_single_region(self, region: str, keyword: str, jwt_token: str) -> Dict[str, Any]:
        """
        Search a single region

        Args:
            region: Region base URL
            keyword: Search keyword
            jwt_token: JWT token for authentication

        Returns:
            Region search result with region info
        """
        url = f"{region}/api/neptune/ms/service/search"
        headers = {"x-jwt-token": jwt_token}
        params = {
            "keyword": keyword,
            "search_type": "all"
        }

        try:
            logger.debug("Searching region", region=region, keyword=keyword)

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Check if service was found
            if data.get("error_code") == 0 and data.get("data"):
                # Add region info to result
                result = {
                    "region": region,
                    "data": data["data"],
                    "timestamp": datetime.now().isoformat()
                }
                logger.debug("Service found in region", region=region, count=len(data["data"]))
                return result
            else:
                logger.debug("No service found in region", region=region, error_code=data.get("error_code"))
                return {"region": region, "data": [], "error": "No matching service"}

        except httpx.TimeoutException:
            logger.warning("Region search timeout", region=region, keyword=keyword)
            return {"region": region, "error": "Timeout"}

        except httpx.HTTPError as e:
            logger.error("Region search HTTP error", region=region, keyword=keyword, error=str(e))
            return {"region": region, "error": f"HTTP error: {e}"}

        except Exception as e:
            logger.error("Region search unexpected error", region=region, keyword=keyword, error=str(e))
            return {"region": region, "error": f"Unexpected error: {e}"}

    def _select_best_result(self, results: List[Any], keyword: str) -> Optional[Dict[str, Any]]:
        """
        Select the best result from multiple regions

        Args:
            results: List of results from all regions
            keyword: Original search keyword

        Returns:
            Best matching result or None
        """
        valid_results = []

        for result in results:
            # Skip exceptions
            if isinstance(result, Exception):
                logger.warning("Region search threw exception", error=str(result))
                continue

            # Skip error results
            if result.get("error"):
                logger.debug("Region returned error", region=result.get("region"), error=result["error"])
                continue

            # Check if we have matching services
            if result.get("data") and len(result["data"]) > 0:
                # Look for exact PSM match
                for service in result["data"]:
                    if service.get("psm") == keyword:
                        logger.info("Found exact PSM match", region=result["region"], psm=keyword)
                        return {
                            "region": result["region"],
                            "service": service,
                            "match_type": "exact"
                        }

                # Store valid results for fallback
                valid_results.append(result)

        # If no exact match, return first valid result
        if valid_results:
            best = valid_results[0]
            logger.info("Using first valid result as fallback", region=best["region"], count=len(best["data"]))
            return {
                "region": best["region"],
                "service": best["data"][0],  # Take first service
                "match_type": "fallback"
            }

        return None

    async def get_service_details(self, psm: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific PSM

        Args:
            psm: PSM identifier

        Returns:
            Detailed service information
        """
        result = await self.search_service(psm)

        if "error" in result:
            return result

        # Format detailed response
        service = result["service"]
        return {
            "psm": service.get("psm"),
            "description": service.get("description", "No description available"),
            "owners": service.get("owners", "Unknown"),
            "framework": service.get("framework", "Unknown"),
            "deployment_platform": service.get("deployment_platform", "Unknown"),
            "level": service.get("level", "Unknown"),
            "region": result["region"],
            "match_type": result["match_type"],
            "last_updated": service.get("updated_at", "Unknown")
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