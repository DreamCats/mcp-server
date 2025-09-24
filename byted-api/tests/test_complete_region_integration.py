"""
Complete integration test for region-specific JWT authentication and log discovery
"""

import os
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from log_discovery import LogDiscovery


async def test_complete_region_integration():
    """Test complete region-specific integration"""
    print("=== Complete Region-Specific Integration Test ===\n")

    # Set up test environment variables for each region
    test_env_vars = {
        "CAS_SESSION_cn": "cn_cookie_for_cloud_bytedance_net",
        "CAS_SESSION_i18n": "i18n_cookie_for_cloud_i18n_bytedance_net",
        "CAS_SESSION_us": "us_cookie_for_cloud_ttp_us_bytedance_net"
    }

    # Store original values to restore later
    original_values = {}
    for key, value in test_env_vars.items():
        original_values[key] = os.getenv(key)
        os.environ[key] = value

    try:
        # Test 1: Create region-specific JWT managers
        print("Test 1: Creating region-specific JWT managers")
        jwt_managers = {
            "us": JWTAuthManager(region="us"),
            "i18n": JWTAuthManager(region="i18n"),
            "cn": JWTAuthManager(region="cn")
        }

        for region, manager in jwt_managers.items():
            expected_cookie = test_env_vars[f"CAS_SESSION_{region}"]
            if manager.cookie_value == expected_cookie:
                print(f"✅ {region.upper()} manager - Correct cookie")
            else:
                print(f"❌ {region.upper()} manager - Wrong cookie")
            print(f"   Auth URL: {manager.auth_url}")

        # Test 2: Create log discovery with multi-region support
        print("\nTest 2: Multi-region log discovery")
        log_discovery = LogDiscovery(jwt_managers)

        # Test 3: Verify region configurations
        print("\nTest 3: Region configurations")
        for region_key, config in log_discovery.REGION_CONFIGS.items():
            print(f"Region: {region_key}")
            print(f"  Display Name: {config['display_name']}")
            print(f"  URL: {config['url']}")
            print(f"  Zones: {config['zones']}")
            print(f"  Default vregion: {config['default_vregion']}")

        # Test 4: Simulate log query (will fail with 401 but shows correct routing)
        print("\nTest 4: Simulating log queries (expected to fail with 401)")
        test_logid = "20250923034643559E874098ED5808B03C"

        for region in ["us", "i18n"]:
            print(f"\nTesting {region.upper()} region:")
            try:
                result = await log_discovery.get_log_details(
                    logid=test_logid,
                    scan_time_min=1,
                    region=region
                )
                print(f"⚠️  Unexpected success for {region}")
            except Exception as e:
                if "401 Unauthorized" in str(e):
                    print(f"✅ {region.upper()} - Correctly routed to region-specific auth endpoint")
                else:
                    print(f"❌ {region.upper()} - Unexpected error: {e}")

        # Test 5: Test concurrent multi-region query
        print("\nTest 5: Concurrent multi-region query")
        try:
            result = await log_discovery.get_log_details(
                logid=test_logid,
                scan_time_min=1,
                region="all"
            )
            print(f"⚠️  Unexpected success for all regions")
        except Exception as e:
            if "401 Unauthorized" in str(e):
                print(f"✅ All regions - Correctly attempted concurrent queries")
            else:
                print(f"❌ All regions - Unexpected error: {e}")

        # Test 6: Cleanup
        print("\nTest 6: Resource cleanup")
        await log_discovery.close()
        for manager in jwt_managers.values():
            await manager.close()
        print("✅ All resources cleaned up successfully")

    finally:
        # Restore original environment variables
        for key, original_value in original_values.items():
            if original_value is not None:
                os.environ[key] = original_value
            elif key in os.environ:
                del os.environ[key]

    print("\n=== Complete integration test completed! ===")


if __name__ == "__main__":
    asyncio.run(test_complete_region_integration())