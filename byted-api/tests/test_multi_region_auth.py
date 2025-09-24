"""
Test script for multi-region JWT authentication and log discovery
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from log_discovery import LogDiscovery


async def test_multi_region_auth():
    """Test multi-region JWT authentication"""
    try:
        print("=== Testing Multi-Region JWT Authentication ===\n")

        # Create region-specific JWT managers
        jwt_managers = {
            "us": JWTAuthManager(region="us"),
            "i18n": JWTAuthManager(region="i18n")
        }

        # Test each region's auth URL
        for region, manager in jwt_managers.items():
            print(f"Region: {region}")
            print(f"  Auth URL: {manager.auth_url}")
            print(f"  Region attribute: {manager.region}")

        print("\n=== Testing Log Discovery with Multi-Region Auth ===\n")

        # Create log discovery with multi-region JWT support
        log_discovery = LogDiscovery(jwt_managers)

        # Test log discovery functionality
        test_logid = "20250923034643559E874098ED5808B03C"
        test_psm_list = ["oec.live.promotion_core"]

        print(f"Testing log discovery with logid: {test_logid}")
        print(f"PSM List: {test_psm_list}")
        print(f"Regions: us, i18n\n")

        # Test different regions
        regions_to_test = ["us"]

        for region in regions_to_test:
            print(f"Testing region: {region}")
            try:
                result = await log_discovery.get_log_details(
                    logid=test_logid,
                    psm_list=test_psm_list,
                    scan_time_min=10,
                    region=region
                )

                print(f"✅ Success")
                print(f"   Region: {result.get('region_display_name', 'Unknown')} ({result.get('region', 'unknown')})")
                print(f"   Messages: {result.get('total_items', 0)}")

            except Exception as e:
                print(f"❌ Failed: {e}")

            print()  # Empty line between tests

        # Clean up
        await log_discovery.close()
        for manager in jwt_managers.values():
            await manager.close()

        print("=== Multi-region authentication test completed! ===")

    except Exception as e:
        print(f"Error during multi-region auth test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_multi_region_auth())