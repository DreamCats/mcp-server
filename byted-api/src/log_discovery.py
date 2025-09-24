"""
Log Discovery Module for ByteDance MCP Server

This module handles log query functionality for multiple regions (US-TTP and SEA) using logid.
Supports concurrent region queries with intelligent region detection.
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class LogDiscovery:
    """Log Discovery with JWT authentication for multiple regions"""

    # Region configuration
    REGION_CONFIGS = {
        "us": {
            "url": "https://logservice-tx.tiktok-us.org/streamlog/platform/microservice/v1/query/trace",
            "display_name": "us Region",
            "zones": ["US-TTP", "US-TTP2"],
            "default_vregion": "US-TTP,US-TTP2"
        },
        "i18n": {
            "url": "https://logservice-sg.tiktok-row.org/streamlog/platform/microservice/v1/query/trace",
            "display_name": "i18n Region (Singapore)",
            "zones": ["Singapore-Common", "US-East", "Singapore-Central"],
            "default_vregion": "Singapore-Common,US-East,Singapore-Central"
        }
    }

    def __init__(self, jwt_managers: Dict[str, Any]):
        """
        Initialize Log Discovery with multi-region JWT support

        Args:
            jwt_managers: Dictionary mapping region keys to JWTAuthManager instances
                         Expected keys: "us", "i18n" (can also include "cn" if needed)
        """
        self.jwt_managers = jwt_managers

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/json",
            }
        )

    async def query_logs_by_logid(self, logid: str, psm_list: Optional[List[str]] = None,
                                scan_time_min: int = 10,
                                region: str = "all") -> Dict[str, Any]:
        """
        Query logs by logid with multi-region support

        Args:
            logid: Log ID to search for
            psm_list: List of PSM services to filter (optional)
            scan_time_min: Scan time range in minutes (default: 10)
            region: Target region - "auto", "US-TTP", "SEA" (default: "auto")

        Returns:
            Log query results including items with message details

        Raises:
            RuntimeError: If log query fails
        """
        logger.info("Querying logs by logid", logid=logid, psm_list=psm_list,
                   scan_time_min=scan_time_min, region=region)

        # Determine target regions
        if region == "all":
            regions_to_query = list(self.REGION_CONFIGS.keys())
        elif region in self.REGION_CONFIGS:
            regions_to_query = [region]
        else:
            # Fallback to all regions for unknown region parameter
            regions_to_query = list(self.REGION_CONFIGS.keys())

        # Query single or multiple regions based on configuration
        if len(regions_to_query) == 1:
            return await self.query_single_region(
                regions_to_query[0], logid, psm_list, scan_time_min
            )
        else:
            return await self.query_all_regions(logid, psm_list, scan_time_min)

    async def query_single_region(self, region_key: str, logid: str, psm_list: Optional[List[str]] = None,
                                  scan_time_min: int = 10) -> Dict[str, Any]:
        """
        Query logs from a single region

        Args:
            region_key: Region key from REGION_CONFIGS
            logid: Log ID to search for
            psm_list: List of PSM services to filter (optional)
            scan_time_min: Scan time range in minutes (default: 10)

        Returns:
            Log query results
        """
        config = self.REGION_CONFIGS[region_key]
        region_url = config["url"]
        default_vregion = config["default_vregion"]

        # Use provided vregion or region default

        logger.info("Querying single region", region=region_key, logid=logid, vregion=default_vregion)

        # Get JWT token for the specific region
        jwt_manager = self.jwt_managers.get(region_key)
        if not jwt_manager:
            logger.error(f"No JWT manager configured for region: {region_key}")
            raise RuntimeError(f"No JWT manager configured for region: {region_key}")

        jwt_token = await jwt_manager.get_jwt_token()

        # Prepare request body
        request_body = {
            "logid": logid,
            "psm_list": psm_list if psm_list else [],
            "scan_span_in_min": scan_time_min,
            "vregion": default_vregion
        }

        # Prepare headers
        headers = {
            "X-Jwt-Token": jwt_token,
            "accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
        }

        try:
            # logger.debug("Querying log service API", region=region_key, url=region_url,
            #             logid=logid, headers=headers, body=request_body)

            response = await self.client.post(region_url, headers=headers, json=request_body)
            response.raise_for_status()

            data = response.json()

            # Format response with region information
            result = {
                "logid": logid,
                "region": region_key,
                "region_display_name": config["display_name"],
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            # Count log items
            items_count = len(data.get("data", {}).get("items", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("Log query completed", region=region_key, logid=logid,
                       items_found=items_count, status_code=response.status_code)
            return result

        except httpx.TimeoutException:
            logger.warning("Log query timeout", region=region_key, logid=logid)
            raise RuntimeError(f"Timeout while querying logs for logid: {logid} in region {region_key}")

        except httpx.HTTPError as e:
            logger.error("Log query HTTP error", region=region_key, logid=logid,
                        error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while querying logs for logid {logid} in region {region_key}: {e}")

        except Exception as e:
            logger.error("Log query unexpected error", region=region_key, logid=logid,
                        error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while querying logs for logid {logid} in region {region_key}: {e}")

    async def query_all_regions(self, logid: str, psm_list: Optional[List[str]] = None,
                              scan_time_min: int = 10, vregion: str = "") -> Dict[str, Any]:
        """
        Query logs from all regions concurrently

        Args:
            logid: Log ID to search for
            psm_list: List of PSM services to filter (optional)
            scan_time_min: Scan time range in minutes (default: 10)
            vregion: Virtual region to search

        Returns:
            Combined log query results from all regions
        """
        logger.info("Querying all regions concurrently", logid=logid, psm_list=psm_list,
                   scan_time_min=scan_time_min, vregion=vregion)

        # Create concurrent tasks for all regions
        tasks = []
        for region_key in self.REGION_CONFIGS.keys():
            task = self.query_single_region(region_key, logid, psm_list, scan_time_min)
            tasks.append(task)

        # Execute concurrent requests
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and select best one
        return self._select_best_result(results, logid)

    def _select_best_result(self, results: List[Any], logid: str) -> Dict[str, Any]:
        """
        Select the best result from multiple region queries

        Args:
            results: List of results from different regions
            logid: Log ID that was queried

        Returns:
            Best result with region information
        """
        valid_results = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(str(result))
                logger.warning(f"Region query failed", region_index=i, error=str(result))
            elif isinstance(result, dict) and "data" in result:
                # Check if we found any log messages
                data = result.get("data", {})
                items_count = len(data.get("data", {}).get("items", [])) if isinstance(data, dict) and "data" in data else 0
                if items_count > 0:
                    valid_results.append(result)
                    logger.info(f"Region found logs", region=result.get("region"), items_count=items_count)
                else:
                    logger.info(f"Region found no logs", region=result.get("region"))

        # Return best result (first one with logs) or fallback
        if valid_results:
            best_result = valid_results[0]
            logger.info("Selected best region result", region=best_result.get("region"),
                       total_regions_queried=len(results), successful_regions=len(valid_results))
            return best_result
        elif errors:
            # If all failed, return error from first failed region
            logger.error("All region queries failed", logid=logid, errors_count=len(errors))
            raise RuntimeError(f"All region queries failed for logid {logid}: {errors[0]}")
        else:
            # All succeeded but no logs found
            logger.warning("No logs found in any region", logid=logid)
            # Return first result with empty data
            if results and isinstance(results[0], dict):
                return results[0]
            else:
                return {
                    "logid": logid,
                    "region": "unknown",
                    "region_display_name": "Unknown Region",
                    "data": {"data": {"items": []}},
                    "timestamp": datetime.now().isoformat()
                }

    def extract_log_messages(self, log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract log messages from the API response

        Args:
            log_data: Raw log data from API response

        Returns:
            List of extracted log messages with key information
        """
        messages = []

        if not isinstance(log_data, dict) or "data" not in log_data:
            return messages

        data = log_data.get("data", {})
        items = data.get("items", [])

        for item in items:
            if not isinstance(item, dict):
                continue

            # Extract basic item information
            item_info = {
                "id": item.get("id", ""),
                "group": item.get("group", {}),
                "values": []
            }

            # Extract values from kv_list
            values = item.get("value", [])
            for value in values:
                if not isinstance(value, dict):
                    continue

                kv_list = value.get("kv_list", [])
                for kv in kv_list:
                    if not isinstance(kv, dict):
                        continue

                    key = kv.get("key", "")
                    value_str = kv.get("value", "")

                    # Focus on _msg field as specified in requirements
                    if key == "_msg":
                        item_info["values"].append({
                            "key": key,
                            "value": value_str,
                            "type": kv.get("type", ""),
                            "highlight": kv.get("highlight", False)
                        })

            # Only include items that have _msg values
            if item_info["values"]:
                messages.append(item_info)

        return messages

    async def get_log_details(self, logid: str, psm_list: Optional[List[str]] = None,
                            scan_time_min: int = 10, region: str = "all") -> Dict[str, Any]:
        """
        Get detailed log information for a specific logid

        Args:
            logid: Log ID to search for
            psm_list: List of PSM services to filter (optional)
            scan_time_min: Scan time range in minutes (default: 10)
            vregion: Virtual region to search (default: "")

        Returns:
            Detailed log information with extracted messages
        """
        result = await self.query_logs_by_logid(logid, psm_list, scan_time_min, region)

        # Extract log messages
        data = result.get("data", {})
        messages = self.extract_log_messages(data)

        # Get metadata
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        tag_infos = data.get("tag_infos", []) if isinstance(data, dict) else []

        return {
            "logid": logid,
            "messages": messages,
            "meta": meta,
            "tag_infos": tag_infos,
            "total_items": len(messages),
            "scan_time_range": meta.get("scan_time_range", []),
            "level_list": meta.get("level_list", []),
            "timestamp": result.get("timestamp", "Unknown")
        }

    def format_log_response(self, log_details: Dict[str, Any]) -> str:
        """
        Format log details into a readable response with region information

        Args:
            log_details: Detailed log information

        Returns:
            Formatted string response
        """
        messages = log_details.get("messages", [])
        total_items = log_details.get("total_items", 0)
        logid = log_details.get("logid", "Unknown")
        scan_time_range = log_details.get("scan_time_range", [])
        region = log_details.get("region", "unknown")
        region_display_name = log_details.get("region_display_name", "Unknown Region")

        response = f"""
📋 **Log Query Results**
🔍 **Log ID**: {logid}
🌍 **Region**: {region_display_name} ({region})
📊 **Total Messages**: {total_items}
"""

        # Add scan time range information
        if scan_time_range:
            response += "⏰ **Scan Time Ranges**:\n"
            for i, time_range in enumerate(scan_time_range, 1):
                start_time = datetime.fromtimestamp(time_range.get("start", 0)).strftime("%Y-%m-%d %H:%M:%S") if time_range.get("start") else "Unknown"
                end_time = datetime.fromtimestamp(time_range.get("end", 0)).strftime("%Y-%m-%d %H:%M:%S") if time_range.get("end") else "Unknown"
                response += f"  Range {i}: {start_time} to {end_time}\n"

        # Add log messages
        if messages:
            response += "\n📝 **Log Messages**:\n"
            for i, message in enumerate(messages, 1):
                group = message.get("group", {})
                psm = group.get("psm", "Unknown")
                pod_name = group.get("pod_name", "Unknown")
                ipv4 = group.get("ipv4", "Unknown")
                env = group.get("env", "Unknown")
                vregion = group.get("vregion", "Unknown")
                idc = group.get("idc", "Unknown")

                response += f"\n--- Message {i} ---\n"
                response += f"  🏷️ **PSM**: {psm}\n"
                response += f"  🐳 **Pod**: {pod_name}\n"
                response += f"  🌐 **IP**: {ipv4}\n"
                response += f"  🌍 **Virtual Region**: {vregion}\n"
                response += f"  🏢 **IDC**: {idc}\n"
                response += f"  🔧 **Environment**: {env}\n"

                # Add message values
                values = message.get("values", [])
                for value in values:
                    if value.get("key") == "_msg":
                        response += f"  💬 **Message**: {value.get('value', 'No message')}\n"
                        if value.get("highlight"):
                            response += "  ✨ **Highlighted**: Yes\n"
        else:
            response += "\n❌ **No log messages found**\n"

        # Add timestamp
        response += f"\n⏰ **Query Time**: {log_details.get('timestamp', 'Unknown')}"

        return response.strip()

    async def close(self):
        """Close HTTP client and all JWT managers"""
        await self.client.aclose()
        # Close all JWT managers
        for jwt_manager in self.jwt_managers.values():
            await jwt_manager.close()

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if hasattr(self, 'client'):
                import asyncio
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.client.aclose())
        except Exception:
            pass