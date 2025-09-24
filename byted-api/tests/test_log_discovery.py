"""
Test script for the new log query functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from log_discovery import LogDiscovery


async def test_log_query():
    """Test the log query functionality"""
    try:
        # Initialize components
        auth_manager = JWTAuthManager()
        log_discovery = LogDiscovery(auth_manager)

        # Test logid from the example in 诉求.md
        test_logid = "20250923034643559E874098ED5808B03C"
        test_psm_list = ["oec.live.promotion_core"]

        print(f"=== Testing Log Query Functionality ===\n")
        print(f"Test Log ID: {test_logid}")
        print(f"Test PSM List: {test_psm_list}\n")

        # Test 1: Query logs with specific PSM
        print("Test 1: Querying logs with specific PSM...")
        result = await log_discovery.get_log_details(
            logid=test_logid,
            psm_list=test_psm_list,
            scan_time_min=10,
            vregion="US-TTP,US-TTP2"
        )

        print(f"Found {result['total_items']} log messages")
        print(f"Messages: {result['messages']}\n")

        # Test 2: Format the response
        print("Test 2: Formatting log response...")
        formatted_response = log_discovery.format_log_response(result)
        print(formatted_response)

        # Test 3: Query logs without PSM filter
        print("\nTest 3: Querying logs without PSM filter...")
        result2 = await log_discovery.get_log_details(
            logid=test_logid,
            scan_time_min=5,
            vregion="US-TTP,US-TTP2"
        )

        print(f"Found {result2['total_items']} log messages (no PSM filter)")

        # Clean up
        await log_discovery.close()
        await auth_manager.close()

        print("\n=== Log query test completed successfully! ===")

    except Exception as e:
        print(f"Error during log query test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_log_query())