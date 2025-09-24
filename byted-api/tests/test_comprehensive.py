"""
Comprehensive test script for all discovery modules
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from cluster_discovery import ClusterDiscovery
from instance_discovery import InstanceDiscovery


async def test_comprehensive_discovery():
    """Test the complete discovery workflow"""
    try:
        # Initialize components
        auth_manager = JWTAuthManager()
        cluster_discovery = ClusterDiscovery(auth_manager)
        instance_discovery = InstanceDiscovery(auth_manager)

        # Test PSM
        psm = "oec.affiliate.monitor"
        print(f"=== Comprehensive Discovery Test for PSM: {psm} ===\n")

        # Step 1: Discover clusters
        print("Step 1: Discovering clusters...")
        cluster_result = await cluster_discovery.get_cluster_details(psm)
        print(f"Found {len(cluster_result['clusters'])} clusters")
        print(f"Region: {cluster_result['region']}")
        print(f"Clusters: {cluster_result['clusters']}\n")

        # Step 2: If clusters found, discover instances for the first cluster
        if cluster_result['clusters']:
            first_cluster = cluster_result['clusters'][0]
            zone = first_cluster['zone']
            idc = first_cluster['idc']
            cluster = first_cluster['cluster']

            print(f"Step 2: Discovering instances for cluster: {cluster}")
            print(f"Zone: {zone}, IDC: {idc}, Cluster: {cluster}")

            instance_result = await instance_discovery.get_instance_details(
                psm, zone, idc, cluster
            )
            print(f"Found {len(instance_result['instances'])} instances")
            print(f"Instances: {instance_result['instances']}\n")

            # Step 3: Test different cluster
            print("Step 3: Discovering instances for Singapore cluster...")
            sg_cluster = cluster_result['clusters'][1]  # Get Singapore cluster
            sg_zone = sg_cluster['zone']
            sg_idc = sg_cluster['idc']
            sg_cluster_name = sg_cluster['cluster']

            sg_instance_result = await instance_discovery.get_instance_details(
                psm, sg_zone, sg_idc, sg_cluster_name
            )
            print(f"Found {len(sg_instance_result['instances'])} instances in Singapore")
            print(f"Singapore instances: {sg_instance_result['instances']}")

        # Clean up
        await cluster_discovery.close()
        await instance_discovery.close()
        await auth_manager.close()

        print("\n=== Test completed successfully! ===")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_comprehensive_discovery())