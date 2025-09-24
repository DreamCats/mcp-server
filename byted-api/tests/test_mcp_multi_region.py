"""
Test script for MCP multi-region log query tool integration
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server import create_server


async def test_mcp_multi_region_tool():
    """Test the MCP multi-region log query tool"""
    try:
        print("=== Testing MCP Multi-Region Log Query Tool ===\n")

        # Create server instance
        server = create_server()

        # Test logid from the example in 诉求.md
        test_logid = "20250923034643559E874098ED5808B03C"
        test_psm_list = "oec.live.promotion_core,oec.affiliate.monitor"

        print(f"Testing MCP tool with:")
        print(f"  Log ID: {test_logid}")
        print(f"  PSM List: {test_psm_list}\n")

        # Test different usage scenarios
        test_scenarios = [
            {
                "name": "Default behavior (all regions)",
                "params": {
                    "logid": test_logid,
                    "psm_list": test_psm_list,
                    "scan_time_min": 10
                    # region defaults to "all"
                }
            },
            {
                "name": "Force US-TTP region",
                "params": {
                    "logid": test_logid,
                    "psm_list": test_psm_list,
                    "scan_time_min": 10,
                    "region": "US-TTP"
                }
            },
            {
                "name": "Force SEA region",
                "params": {
                    "logid": test_logid,
                    "psm_list": test_psm_list,
                    "scan_time_min": 10,
                    "region": "SEA"
                }
            },
            {
                "name": "Explicit all regions",
                "params": {
                    "logid": test_logid,
                    "psm_list": test_psm_list,
                    "scan_time_min": 10,
                    "region": "all"
                }
            },
            {
                "name": "Simple logid only",
                "params": {
                    "logid": test_logid
                    # All other parameters use defaults
                }
            }
        ]

        # Test the underlying functionality directly
        from log_discovery import LogDiscovery
        from auth import JWTAuthManager

        # Create multi-region JWT managers
        jwt_managers = {
            "us": JWTAuthManager(region="us"),
            "i18n": JWTAuthManager(region="i18n")
        }
        log_discovery = LogDiscovery(jwt_managers)

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"Test {i}: {scenario['name']}")
            try:
                # Extract parameters
                params = scenario['params']
                logid = params['logid']
                psm_list = params.get('psm_list', None)
                scan_time_min = params.get('scan_time_min', 10)
                region = params.get('region', 'all')  # Default changed to 'all'

                # Parse PSM list
                psm_services = None
                if psm_list:
                    psm_services = [psm.strip() for psm in psm_list.split(",") if psm.strip()]

                # Query logs
                result = await log_discovery.get_log_details(
                    logid=logid,
                    psm_list=psm_services,
                    scan_time_min=scan_time_min,
                    region=region
                )

                # Format response
                formatted_response = log_discovery.format_log_response(result)

                print(f"✅ Success")
                print(f"   Region: {result.get('region_display_name', 'Unknown')} ({result.get('region', 'unknown')})")
                print(f"   Messages: {result.get('total_items', 0)}")
                # Show first few lines of response
                response_lines = formatted_response.split('\n')[:3]
                for line in response_lines:
                    print(f"   {line}")
                if len(response_lines) < len(formatted_response.split('\n')):
                    print("   ...")

            except Exception as e:
                print(f"❌ Failed: {e}")

            print()  # Empty line between tests

        # Test parameter validation
        print("Parameter Validation Tests:")
        validation_tests = [
            ("Invalid region", {"logid": test_logid, "region": "INVALID"}),
            ("Empty logid", {"logid": ""}),
            ("Very short scan time", {"logid": test_logid, "scan_time_min": 1}),
            ("Long scan time", {"logid": test_logid, "scan_time_min": 60}),
        ]

        for test_name, params in validation_tests:
            print(f"Test: {test_name}")
            try:
                psm_services = params.get('psm_list', '').split(",") if params.get('psm_list') else None
                result = await log_discovery.get_log_details(
                    logid=params['logid'],
                    psm_list=psm_services,
                    scan_time_min=params.get('scan_time_min', 10),
                    region=params.get('region', 'all')  # Default changed to 'all'
                )
                print(f"✅ Handled gracefully")
            except Exception as e:
                print(f"✅ Error properly caught: {type(e).__name__}")

        # Clean up
        await log_discovery.close()

        print("\n=== MCP multi-region tool test completed! ===")

    except Exception as e:
        print(f"Error during MCP multi-region test: {e}")
        import traceback
        traceback.print_exc()


async def test_tool_signature_examples():
    """Test the examples from the tool signature"""
    print("\n=== Testing Tool Signature Examples ===")

    from log_discovery import LogDiscovery
    from auth import JWTAuthManager

    # Create multi-region JWT managers
    jwt_managers = {
        "us": JWTAuthManager(region="us"),
        "i18n": JWTAuthManager(region="i18n")
    }
    log_discovery = LogDiscovery(jwt_managers)

    test_logid = "20250923034643559E874098ED5808B03C"

    examples = [
        {
            "name": "Default behavior (all regions)",
            "call": lambda: log_discovery.get_log_details(logid=test_logid)
        },
        {
            "name": "Force specific region",
            "call": lambda: log_discovery.get_log_details(logid=test_logid, region="SEA")
        },
        {
            "name": "With PSM filtering",
            "call": lambda: log_discovery.get_log_details(
                logid=test_logid,
                psm_list=["oec.live.promotion_core"]
            )
        },
        {
            "name": "Query all regions explicitly",
            "call": lambda: log_discovery.get_log_details(logid=test_logid, region="all")
        }
    ]

    for example in examples:
        print(f"\nExample: {example['name']}")
        try:
            result = await example['call']()
            print(f"✅ Success - Region: {result.get('region_display_name', 'Unknown')}")
            print(f"   Messages found: {result.get('total_items', 0)}")
        except Exception as e:
            print(f"❌ Failed: {e}")

    # Clean up
    await log_discovery.close()


if __name__ == "__main__":
    asyncio.run(test_tool_signature_examples())
    asyncio.run(test_mcp_multi_region_tool())