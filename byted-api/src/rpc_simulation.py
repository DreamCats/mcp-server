"""
i18n RPC Request Simulation Module for ByteDance MCP Server

This module handles RPC request simulation for TikTok ROW environments using discovered instance addresses.
"""

import json
from typing import Dict, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class RPCSimulator:
    """i18n RPC Request Simulation with JWT authentication"""

    def __init__(self, jwt_manager):
        """
        Initialize RPC Simulator

        Args:
            jwt_manager: JWTAuthManager instance for authentication
        """
        self.jwt_manager = jwt_manager
        self.rpc_url = "https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/rpc_request"

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=60.0,  # Longer timeout for RPC requests
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/json",
            }
        )

    async def simulate_rpc_request(self, psm: str, address: str, func_name: str,
                                 req_body: str, zone: str, idc: str,
                                 cluster: str = "default", env: str = "prod",
                                 request_timeout: int = 60000, idl_source: int = 1,
                                 idl_version: str = "master") -> Dict[str, Any]:
        """
        Simulate RPC request to i18n service using discovered instance address

        Args:
            psm: PSM identifier (required, e.g., "oec.affiliate.monitor")
            address: Target instance address in format [ip]:port (required)
            func_name: RPC method name to call (required, e.g., "SearchLiveEvent")
            req_body: JSON string request body (required)
            zone: Geographic zone identifier (required, e.g., "MVAALI", "SGALI")
            idc: Data center identifier (required, e.g., "maliva", "my", "sg1")
            cluster: Cluster name (optional, defaults to "default")
            env: Environment (optional, defaults to "prod")
            request_timeout: Request timeout in milliseconds (optional, defaults to 60000)
            idl_source: IDL source (optional, defaults to 1)
            idl_version: IDL version (optional, defaults to "master")

        Returns:
            RPC response including resp_body, performance metrics, and debug information

        Raises:
            RuntimeError: If RPC request simulation fails

        Example:
            >>> result = await simulator.simulate_rpc_request(
            ...     psm="oec.affiliate.monitor",
            ...     address="[fdbd:dc61:2:151::195]:11503",
            ...     func_name="SearchLiveEvent",
            ...     req_body='{"room_id": "1730849136927543871", "author_id": "7280819145410593838"}',
            ...     zone="MVAALI",
            ...     idc="maliva"
            ... )
        """
        logger.info("Simulating RPC request",
                   psm=psm, address=address, func_name=func_name,
                   zone=zone, idc=idc, cluster=cluster, env=env)

        # Get JWT token
        jwt_token = await self.jwt_manager.get_jwt_token()

        # Prepare request body
        request_body = {
            "psm": psm,
            "func_name": func_name,
            "req_body": req_body,
            "idl_source": idl_source,
            "idl_version": idl_version,
            "zone": zone,
            "idc": idc,
            "cluster": cluster,
            "env": env,
            "address": address,
            "rpc_context": [],
            "request_timeout": request_timeout,
            "connect_timeout": request_timeout,  # Same as request timeout
            "online": True,
            "source": 1,
            "base": {}
        }

        headers = {"x-jwt-token": jwt_token}

        try:
            logger.debug("Sending RPC request",
                        url=self.rpc_url,
                        headers=headers,
                        request_body=request_body)

            response = await self.client.post(self.rpc_url, headers=headers, json=request_body)
            response.raise_for_status()

            data = response.json()

            # Log response details for debugging
            logger.debug("RPC simulation response",
                        status_code=response.status_code,
                        response_headers=dict(response.headers),
                        response_data=data)

            # Format response
            result = {
                "psm": psm,
                "address": address,
                "func_name": func_name,
                "zone": zone,
                "idc": idc,
                "cluster": cluster,
                "env": env,
                "request_data": request_body,
                "response_data": data,
                "timestamp": datetime.now().isoformat()
            }

            # Extract key metrics
            if isinstance(data, dict) and "data" in data:
                response_data = data.get("data", {})

                # Extract performance metrics
                if isinstance(response_data, dict):
                    result["performance"] = {
                        "request_latency": response_data.get("req_latency"),
                        "request_at": response_data.get("request_at"),
                        "finish_at": response_data.get("finish_at"),
                        "protocol": response_data.get("protocol")
                    }

                    # Extract response body if available
                    resp_body = response_data.get("resp_body")
                    if resp_body:
                        try:
                            # Try to parse as JSON for better formatting
                            parsed_resp = json.loads(resp_body)
                            result["response_body"] = parsed_resp
                        except json.JSONDecodeError:
                            # Keep as string if not valid JSON
                            result["response_body"] = resp_body

                    # Extract debug information
                    debug_info = response_data.get("debug_info", {})
                    if debug_info:
                        result["debug_info"] = debug_info

                    # Extract business status
                    result["business_status"] = {
                        "biz_status_code": response_data.get("biz_status_code"),
                        "error_message": response_data.get("error"),
                        "help_message": response_data.get("help_message")
                    }

            logger.info("RPC simulation completed",
                       psm=psm,
                       func_name=func_name,
                       status_code=response.status_code,
                       has_response_body="response_body" in result)

            return result

        except httpx.TimeoutException:
            logger.error("RPC simulation timeout", psm=psm, address=address, timeout=request_timeout)
            raise RuntimeError(f"Timeout while simulating RPC request to {address} (timeout: {request_timeout}ms)")

        except httpx.HTTPError as e:
            logger.error("RPC simulation HTTP error",
                        psm=psm,
                        address=address,
                        error=str(e),
                        error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while simulating RPC request to {address}: {e}")

        except json.JSONDecodeError as e:
            logger.error("RPC simulation JSON error",
                        psm=psm,
                        address=address,
                        error=str(e))
            raise RuntimeError(f"JSON error while processing RPC request/response: {e}")

        except Exception as e:
            logger.error("RPC simulation unexpected error",
                        psm=psm,
                        address=address,
                        error=str(e),
                        error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while simulating RPC request to {address}: {e}")

    async def simulate_rpc_with_discovery(self, psm: str, func_name: str, req_body: str,
                                        zone: str, idc: str, cluster: str = "default",
                                        **kwargs) -> Dict[str, Any]:
        """
        Convenience method that combines instance discovery with RPC simulation

        Args:
            psm: PSM identifier
            func_name: RPC method name to call
            req_body: JSON string request body
            zone: Geographic zone identifier
            idc: Data center identifier
            cluster: Cluster name (optional, defaults to "default")
            **kwargs: Additional parameters for RPC simulation

        Returns:
            Combined result with instance discovery and RPC simulation

        Note:
            This method requires the instance_discovery module to be available
        """
        try:
            # Import here to avoid circular dependencies
            from instance_discovery import InstanceDiscovery

            # Create instance discovery instance
            instance_discovery = InstanceDiscovery(self.jwt_manager)

            # Discover instances
            logger.info("Auto-discovering instances for RPC simulation", psm=psm, zone=zone, idc=idc)
            instances_result = await instance_discovery.get_instance_details(psm, zone, idc, cluster)

            instances = instances_result.get("instances", [])
            if not instances:
                raise RuntimeError(f"No instances found for PSM: {psm} in zone: {zone}, idc: {idc}")

            # Use first available instance
            first_instance = instances[0]
            if isinstance(first_instance, str):
                address = first_instance
            else:
                # Handle dictionary format if needed
                address = str(first_instance)

            logger.info("Using discovered instance for RPC simulation", address=address)

            # Simulate RPC request
            rpc_result = await self.simulate_rpc_request(
                psm=psm,
                address=address,
                func_name=func_name,
                req_body=req_body,
                zone=zone,
                idc=idc,
                cluster=cluster,
                **kwargs
            )

            # Combine results
            return {
                "discovery": {
                    "instances_found": len(instances),
                    "used_instance": address,
                    "all_instances": instances
                },
                "rpc_simulation": rpc_result,
                "timestamp": datetime.now().isoformat()
            }

        except ImportError:
            logger.error("InstanceDiscovery module not available for auto-discovery")
            raise RuntimeError("InstanceDiscovery module required for auto-discovery feature")

        except Exception as e:
            logger.error("Auto-discovery RPC simulation failed", error=str(e))
            raise RuntimeError(f"Auto-discovery RPC simulation failed: {e}")

    def format_rpc_response(self, result: Dict[str, Any]) -> str:
        """
        Format RPC simulation result for user-friendly display

        Args:
            result: RPC simulation result dictionary

        Returns:
            Formatted string for display
        """
        rpc_data = result.get("rpc_simulation", result)  # Handle both formats

        response = f"""
🚀 **RPC Simulation Results**
🔧 **PSM**: {rpc_data.get("psm", "Unknown")}
🎯 **Function**: {rpc_data.get("func_name", "Unknown")}
🌐 **Address**: {rpc_data.get("address", "Unknown")}
🌍 **Zone**: {rpc_data.get("zone", "Unknown")}
🏢 **IDC**: {rpc_data.get("idc", "Unknown")}
"""

        # Add performance metrics if available
        performance = rpc_data.get("performance", {})
        if performance:
            response += f"\n⚡ **Performance**:\n"
            if performance.get("request_latency"):
                response += f"  Latency: {performance['request_latency']}\n"
            if performance.get("protocol"):
                response += f"  Protocol: {performance['protocol']}\n"

        # Add business status if available
        business_status = rpc_data.get("business_status", {})
        if business_status:
            response += f"\n📊 **Business Status**:\n"
            if business_status.get("biz_status_code") is not None:
                response += f"  Status Code: {business_status['biz_status_code']}\n"
            if business_status.get("error_message"):
                response += f"  Error: {business_status['error_message']}\n"

        # Add response body if available
        response_body = rpc_data.get("response_body")
        if response_body:
            response += f"\n📄 **Response Body**:\n"
            if isinstance(response_body, dict):
                # Pretty print JSON response
                response += json.dumps(response_body, indent=2, ensure_ascii=False)
            else:
                response += str(response_body)

        # Add debug info if available
        debug_info = rpc_data.get("debug_info")
        if debug_info:
            response += f"\n\n🔍 **Debug Information**:\n"
            response += json.dumps(debug_info, indent=2, ensure_ascii=False)

        response += f"\n\n⏰ **Timestamp**: {rpc_data.get('timestamp', 'Unknown')}"

        return response.strip()

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