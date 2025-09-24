"""
Comprehensive test script for multi-region log query functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from log_discovery import LogDiscovery


async def test_multi_region_functionality():
    """Test the complete multi-region log query functionality"""
    try:
        # Initialize components with multi-region JWT support
        jwt_managers = {
            "us": JWTAuthManager(region="us"),
            "i18n": JWTAuthManager(region="i18n")
        }
        log_discovery = LogDiscovery(jwt_managers)

        # Test logid from the example in 诉求.md
        test_logid = "20250923034643559E874098ED5808B03C"
        test_psm_list = ["oec.live.promotion_core"]

        print(f"=== Testing Multi-Region Log Query Functionality ===\n")
        print(f"Test Log ID: {test_logid}")
        print(f"Test PSM List: {test_psm_list}\n")

        # Test 1: Default behavior (query all regions)
        print("Test 1: Default behavior - query all regions...")
        try:
            result = await log_discovery.get_log_details(
                logid=test_logid,
                psm_list=test_psm_list,
                scan_time_min=10
                # region defaults to "all"
            )
            print(f"✅ All regions query successful")
            print(f"   Region: {result.get('region_display_name', 'Unknown')} ({result.get('region', 'unknown')})")
            print(f"   Messages found: {result.get('total_items', 0)}")
        except Exception as e:
            print(f"❌ All regions query failed: {e}")

        # Test 2: Force US-TTP region
        print("\nTest 2: Force US-TTP region...")
        try:
            result = await log_discovery.get_log_details(
                logid=test_logid,
                psm_list=test_psm_list,
                scan_time_min=10,
                region="US-TTP"
            )
            print(f"✅ US-TTP query successful")
            print(f"   Region: {result.get('region_display_name', 'Unknown')}")
            print(f"   Messages found: {result.get('total_items', 0)}")
        except Exception as e:
            print(f"❌ US-TTP query failed: {e}")

        # Test 3: Force SEA region
        print("\nTest 3: Force SEA region...")
        try:
            result = await log_discovery.get_log_details(
                logid=test_logid,
                psm_list=test_psm_list,
                scan_time_min=10,
                region="SEA"
            )
            print(f"✅ SEA query successful")
            print(f"   Region: {result.get('region_display_name', 'Unknown')}")
            print(f"   Messages found: {result.get('total_items', 0)}")
        except Exception as e:
            print(f"❌ SEA query failed: {e}")

        # Test 4: Explicitly query all regions (same as default)
        print("\nTest 4: Explicitly query all regions...")
        try:
            result = await log_discovery.get_log_details(
                logid=test_logid,
                psm_list=test_psm_list,
                scan_time_min=10,
                region="all"
            )
            print(f"✅ Explicit all regions query successful")
            print(f"   Region: {result.get('region_display_name', 'Unknown')}")
            print(f"   Messages found: {result.get('total_items', 0)}")
        except Exception as e:
            print(f"❌ Explicit all regions query failed: {e}")

        # Test 5: Test region configurations
        print("\nTest 5: Test available regions...")
        print(f"Available regions: {list(log_discovery.REGION_CONFIGS.keys())}")
        for region_key, config in log_discovery.REGION_CONFIGS.items():
            print(f"   {region_key}: {config['display_name']}")
            print(f"      Zones: {config['zones']}")
            print(f"      Default vregion: {config['default_vregion']}")

        # Test 6: Test with different scan times
        print("\nTest 6: Test different scan times...")
        scan_time_tests = [1, 5, 10, 30]
        for scan_time in scan_time_tests:
            try:
                result = await log_discovery.get_log_details(
                    logid=test_logid,
                    psm_list=test_psm_list,
                    scan_time_min=scan_time
                )
                print(f"✅ Scan time {scan_time}min: {result.get('total_items', 0)} messages found")
            except Exception as e:
                print(f"❌ Scan time {scan_time}min failed: {e}")

        # Test 7: Format response
        print("\nTest 7: Test response formatting...")
        try:
            # Get a result to format (using default all regions)
            result = await log_discovery.get_log_details(
                logid=test_logid,
                psm_list=test_psm_list,
                scan_time_min=10
                # region defaults to "all"
            )
            formatted = log_discovery.format_log_response(result)
            print("✅ Response formatting successful")
            print("   Sample formatted output:")
            # Show first few lines of formatted response
            lines = formatted.split('\n')[:5]
            for line in lines:
                print(f"   {line}")
            if len(lines) < len(formatted.split('\n')):
                print("   ...")
        except Exception as e:
            print(f"❌ Response formatting failed: {e}")

        # Test 8: Error handling
        print("\nTest 8: Test error handling...")
        error_tests = [
            ("invalid-logid", "Invalid logid"),
            ("", "Empty logid"),
        ]

        for invalid_logid, description in error_tests:
            try:
                result = await log_discovery.get_log_details(
                    logid=invalid_logid,
                    scan_time_min=1,
                    region="US-TTP"
                )
                print(f"⚠️  {description} test - no error raised (unexpected)")
            except Exception as e:
                print(f"✅ {description} test - error properly handled: {type(e).__name__}")

        # Clean up
        await log_discovery.close()

        print("\n=== Multi-region functionality test completed! ===")

    except Exception as e:
        print(f"Error during multi-region test: {e}")
        import traceback
        traceback.print_exc()


async def test_region_configurations():
    """Test the region configurations"""
    print("\n=== Testing Region Configurations ===")

    from log_discovery import LogDiscovery

    # Test region configs
    configs = LogDiscovery.REGION_CONFIGS
    print(f"Available regions: {list(configs.keys())}")

    for region_key, config in configs.items():
        print(f"\nRegion: {region_key}")
        print(f"  Display Name: {config['display_name']}")
        print(f"  URL: {config['url']}")
        print(f"  Zones: {config['zones']}")
        print(f"  Default vregion: {config['default_vregion']}")


if __name__ == "__main__":
    asyncio.run(test_region_configurations())
    asyncio.run(test_multi_region_functionality())