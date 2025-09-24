"""
Test script for the Instance Discovery module
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from instance_discovery import InstanceDiscovery


async def test_instance_discovery():
    """Test the instance discovery functionality"""
    try:
        # Initialize components
        auth_manager = JWTAuthManager()
        instance_discovery = InstanceDiscovery(auth_manager)

        # Test with a real PSM and cluster details
        psm = "oec.affiliate.monitor"
        zone = "MVAALI"
        idc = "maliva"
        cluster = "default"

        print(f"Testing instance discovery for PSM: {psm}")
        print(f"Zone: {zone}, IDC: {idc}, Cluster: {cluster}")

        result = await instance_discovery.get_instance_details(psm, zone, idc, cluster)
        print("Instance discovery result:")
        print(result)

        # Test without cluster (should default to "default")
        print("\nTesting without cluster parameter (should default to 'default'):")
        result_no_cluster = await instance_discovery.get_instance_details(psm, zone, idc)
        print("Instance discovery result (no cluster):")
        print(result_no_cluster)

        # Clean up
        await instance_discovery.close()
        await auth_manager.close()

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_instance_discovery())