#!/usr/bin/env python3
"""
Test script for ByteDance MCP Server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.auth import JWTAuthManager
from src.service_discovery import PSMServiceDiscovery


async def test_jwt_auth():
    """Test JWT authentication"""
    print("🧪 Testing JWT Authentication...")

    # Check if CAS_SESSION is set
    cas_session = os.getenv("CAS_SESSION")
    if not cas_session:
        print("❌ CAS_SESSION environment variable not set")
        print("Please set it: export CAS_SESSION=\"your_cookie_value\"")
        return False

    try:
        auth_manager = JWTAuthManager()
        token = await auth_manager.get_jwt_token()
        print(f"✅ JWT token acquired: {token[:20]}...")

        is_valid = auth_manager.is_token_valid()
        print(f"✅ Token validation: {is_valid}")

        await auth_manager.close()
        return True

    except Exception as e:
        print(f"❌ JWT authentication failed: {e}")
        return False


async def test_service_discovery():
    """Test PSM service discovery"""
    print("\n🧪 Testing PSM Service Discovery...")

    cas_session = os.getenv("CAS_SESSION")
    if not cas_session:
        print("❌ CAS_SESSION environment variable not set")
        return False

    try:
        auth_manager = JWTAuthManager()
        service_discovery = PSMServiceDiscovery(auth_manager)

        # Test with a sample service
        test_keywords = ["oec.affiliate.monitor", "test.service"]

        for keyword in test_keywords:
            print(f"\n🔍 Searching for: {keyword}")
            try:
                result = await service_discovery.search_service(keyword)

                if "error" in result:
                    print(f"⚠️  Search result: {result['error']}")
                else:
                    print(f"✅ Service found in region: {result['region']}")
                    if result.get('service'):
                        service = result['service']
                        print(f"   PSM: {service.get('psm', 'N/A')}")
                        print(f"   Description: {service.get('description', 'N/A')}")
                        print(f"   Owners: {service.get('owners', 'N/A')}")

            except Exception as e:
                print(f"❌ Error searching {keyword}: {e}")

        await auth_manager.close()
        await service_discovery.close()
        return True

    except Exception as e:
        print(f"❌ Service discovery failed: {e}")
        return False


async def test_concurrent_search():
    """Test concurrent search functionality"""
    print("\n🧪 Testing Concurrent Search...")

    cas_session = os.getenv("CAS_SESSION")
    if not cas_session:
        print("❌ CAS_SESSION environment variable not set")
        return False

    try:
        auth_manager = JWTAuthManager()
        service_discovery = PSMServiceDiscovery(auth_manager)

        # Test concurrent search with multiple keywords
        keywords = ["oec.affiliate.monitor", "test.service", "demo.service"]

        print(f"🔄 Concurrent search for {len(keywords)} keywords...")

        tasks = []
        for keyword in keywords:
            task = service_discovery.search_service(keyword)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, (keyword, result) in enumerate(zip(keywords, results)):
            if isinstance(result, Exception):
                print(f"❌ {keyword}: Exception - {result}")
            elif "error" in result:
                print(f"⚠️  {keyword}: {result['error']}")
            else:
                print(f"✅ {keyword}: Found in {result['region']}")

        await auth_manager.close()
        await service_discovery.close()
        return True

    except Exception as e:
        print(f"❌ Concurrent search failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting ByteDance MCP Server Tests")
    print("=" * 50)

    # Run tests
    jwt_ok = await test_jwt_auth()
    discovery_ok = await test_service_discovery()
    concurrent_ok = await test_concurrent_search()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"JWT Authentication: {'✅ PASS' if jwt_ok else '❌ FAIL'}")
    print(f"Service Discovery: {'✅ PASS' if discovery_ok else '❌ FAIL'}")
    print(f"Concurrent Search: {'✅ PASS' if concurrent_ok else '❌ FAIL'}")

    if jwt_ok and discovery_ok and concurrent_ok:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)