"""
Test script for the MCP log query tool integration
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server import create_server


async def test_mcp_log_tool():
    """Test the MCP log query tool"""
    try:
        print("=== Testing MCP Log Query Tool ===\n")

        # Create server instance
        server = create_server()

        # Test log query tool
        test_logid = "20250923034643559E874098ED5808B03C"
        test_psm_list = "oec.live.promotion_core,oec.affiliate.monitor"

        print(f"Testing log query with:")
        print(f"  Log ID: {test_logid}")
        print(f"  PSM List: {test_psm_list}")
        print(f"  Scan Time: 10 minutes")
        print(f"  Region: US-TTP,US-TTP2\n")

        # Get the tool function from the server
        # Note: In a real MCP client, this would be called through the MCP protocol
        # For testing, we'll simulate the tool call

        # Simulate the tool parameters
        tool_params = {
            "logid": test_logid,
            "psm_list": test_psm_list,
            "scan_time_min": 10,
            "vregion": "US-TTP,US-TTP2"
        }

        print("Calling query_logs_by_logid tool...")

        # This would normally be called through MCP protocol
        # For now, we'll test the underlying functionality
        from log_discovery import LogDiscovery
        from auth import JWTAuthManager

        auth_manager = JWTAuthManager()
        log_discovery = LogDiscovery(auth_manager)

        # Test the log discovery functionality
        result = await log_discovery.get_log_details(
            logid=tool_params["logid"],
            psm_list=tool_params["psm_list"].split(",") if tool_params["psm_list"] else None,
            scan_time_min=tool_params["scan_time_min"],
            vregion=tool_params["vregion"]
        )

        formatted_response = log_discovery.format_log_response(result)
        print("Tool Response:")
        print(formatted_response)

        # Clean up
        await log_discovery.close()
        await auth_manager.close()

        print("\n=== MCP log query tool test completed! ===")

    except Exception as e:
        print(f"Error during MCP log tool test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_log_tool())