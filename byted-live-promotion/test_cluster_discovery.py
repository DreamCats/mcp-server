"""
Test script for the Cluster Discovery module
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auth import JWTAuthManager
from cluster_discovery import ClusterDiscovery


async def test_cluster_discovery():
    """Test the cluster discovery functionality"""
    try:
        # Initialize components
        auth_manager = JWTAuthManager()
        cluster_discovery = ClusterDiscovery(auth_manager)

        # Test with a real PSM
        psm = "oec.affiliate.monitor"
        print(f"Testing cluster discovery for PSM: {psm}")
        result = await cluster_discovery.get_cluster_details(psm)
        print("Cluster discovery result:")
        print(result)

        # Clean up
        await cluster_discovery.close()
        await auth_manager.close()

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_cluster_discovery())