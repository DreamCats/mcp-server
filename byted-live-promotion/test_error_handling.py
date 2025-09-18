"""
Test error handling for required parameters
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auth import JWTAuthManager
from instance_discovery import InstanceDiscovery


async def test_error_handling():
    """Test error handling for missing required parameters"""
    try:
        # Initialize components
        auth_manager = JWTAuthManager()
        instance_discovery = InstanceDiscovery(auth_manager)

        psm = "oec.affiliate.monitor"

        print("Testing instance discovery with missing zone and idc...")
        try:
            # This should fail because zone and idc are now required
            result = await instance_discovery.get_instance_details(psm)
            print("ERROR: Should have failed with missing parameters!")
        except TypeError as e:
            print(f"✅ Correctly caught TypeError: {e}")

        print("\nTesting instance discovery with only zone...")
        try:
            result = await instance_discovery.get_instance_details(psm, "MVAALI")
            print("ERROR: Should have failed with missing idc!")
        except TypeError as e:
            print(f"✅ Correctly caught TypeError: {e}")

        print("\nTesting instance discovery with all required parameters...")
        result = await instance_discovery.get_instance_details(psm, "MVAALI", "maliva")
        print(f"✅ Success: Found {len(result['instances'])} instances")

        # Clean up
        await instance_discovery.close()
        await auth_manager.close()

        print("\n=== Error handling test completed successfully! ===")

    except Exception as e:
        print(f"Unexpected error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_error_handling())