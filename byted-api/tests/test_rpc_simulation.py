"""
Test script for i18n RPC Request Simulation functionality
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager
from rpc_simulation import RPCSimulator


async def test_rpc_simulation():
    """Test RPC simulation with real example from 诉求.md"""
    try:
        # Initialize components
        auth_manager = JWTAuthManager()
        rpc_simulator = RPCSimulator(auth_manager)

        # Test data from 诉求.md
        psm = "oec.affiliate.monitor"
        address = "[fdbd:dc61:2:151::195]:11503"
        func_name = "SearchLiveEvent"
        zone = "MVAALI"
        idc = "maliva"
        cluster = "default"

        # Request body from 诉求.md example
        request_body = {
            "room_id": "1730849136927543871",
            "author_id": "7280819145410593838",
            "time_selector": {
                "start_timestamp": 1757831992000,
                "end_timestamp": 1758004792000
            },
            "object_id": "1730849136927543871",
            "only_failed_event": False,
            "page": 0,
            "size": 20
        }

        req_body = json.dumps(request_body, ensure_ascii=False)

        print("🚀 Testing RPC Simulation...")
        print(f"📡 PSM: {psm}")
        print(f"🎯 Function: {func_name}")
        print(f"🌐 Address: {address}")
        print(f"🌍 Zone: {zone}")
        print(f"🏢 IDC: {idc}")
        print(f"📦 Cluster: {cluster}")
        print(f"📄 Request Body: {req_body[:100]}...")

        # Test basic RPC simulation
        print("\n" + "="*50)
        print("1. Testing Basic RPC Simulation")
        print("="*50)

        result = await rpc_simulator.simulate_rpc_request(
            psm=psm,
            address=address,
            func_name=func_name,
            req_body=req_body,
            zone=zone,
            idc=idc,
            cluster=cluster
        )

        print("✅ RPC Simulation Result:")
        formatted_result = rpc_simulator.format_rpc_response(result)
        print(formatted_result)

        # Test with auto-discovery
        print("\n" + "="*50)
        print("2. Testing RPC Simulation with Auto-Discovery")
        print("="*50)

        auto_result = await rpc_simulator.simulate_rpc_with_discovery(
            psm=psm,
            func_name=func_name,
            req_body=req_body,
            zone=zone,
            idc=idc,
            cluster=cluster
        )

        print("✅ Auto-Discovery RPC Result:")
        discovery_info = auto_result.get("discovery", {})
        rpc_info = auto_result.get("rpc_simulation", {})

        print(f"🔍 Discovery: Found {discovery_info.get('instances_found', 0)} instances")
        print(f"🎯 Used Instance: {discovery_info.get('used_instance', 'N/A')}")

        if rpc_info:
            formatted_auto_result = rpc_simulator.format_rpc_response(auto_result)
            print("\n📡 RPC Simulation Results:")
            print(formatted_auto_result)

        # Test error handling
        print("\n" + "="*50)
        print("3. Testing Error Handling")
        print("="*50)

        # Test with invalid address
        try:
            await rpc_simulator.simulate_rpc_request(
                psm=psm,
                address="invalid-address",
                func_name=func_name,
                req_body=req_body,
                zone=zone,
                idc=idc
            )
            print("❌ Should have failed with invalid address")
        except Exception as e:
            print(f"✅ Correctly caught error with invalid address: {e}")

        # Clean up
        await rpc_simulator.close()
        await auth_manager.close()

        print("\n" + "="*50)
        print("🎉 All RPC Simulation Tests Completed Successfully!")
        print("="*50)

    except Exception as e:
        print(f"❌ Error during RPC simulation test: {e}")
        import traceback
        traceback.print_exc()


async def test_simple_rpc():
    """Simple test for basic RPC functionality"""
    try:
        auth_manager = JWTAuthManager()
        rpc_simulator = RPCSimulator(auth_manager)

        # Simple test case
        print("🧪 Testing Simple RPC Request...")

        result = await rpc_simulator.simulate_rpc_request(
            psm="oec.affiliate.monitor",
            address="[fdbd:dc61:2:151::195]:11503",
            func_name="SearchLiveEvent",
            req_body='{"room_id": "1730849136927543871", "author_id": "7280819145410593838"}',
            zone="MVAALI",
            idc="maliva"
        )

        print("✅ Simple RPC test completed successfully")
        print(f"📊 Status: Success")
        print(f"🎯 Function: {result.get('func_name')}")
        print(f"🌐 Address: {result.get('address')}")

        # Show formatted response
        formatted = rpc_simulator.format_rpc_response(result)
        print(f"\n📄 Formatted Response:\n{formatted}")

        await rpc_simulator.close()
        await auth_manager.close()

    except Exception as e:
        print(f"❌ Simple RPC test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting RPC Simulation Tests...")
    print("This test will simulate RPC requests to i18n services using discovered instance addresses.")
    print("Make sure you have set the CAS_SESSION environment variable.\n")

    # Run simple test first
    asyncio.run(test_simple_rpc())

    print("\n" + "="*60 + "\n")

    # Run comprehensive test
    asyncio.run(test_rpc_simulation())