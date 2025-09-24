"""
Test script for .env file integration with JWT authentication
"""

import os
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager


async def test_dotenv_integration():
    """Test .env file integration for JWT authentication"""
    print("=== Testing .env File Integration ===\n")

    # Test 1: Verify .env file loading
    print("Test 1: Verify .env file is loaded")

    # Check if environment variables from .env are loaded
    env_vars = ["CAS_SESSION", "CAS_SESSION_cn", "CAS_SESSION_i18n", "CAS_SESSION_us"]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"❌ {var}: Not found")

    # Test 2: Create JWT managers using .env values
    print("\nTest 2: Create JWT managers from .env file")

    try:
        # Create region-specific JWT managers
        jwt_managers = {
            "us": JWTAuthManager(region="us"),
            "i18n": JWTAuthManager(region="i18n"),
            "cn": JWTAuthManager(region="cn")
        }

        for region, manager in jwt_managers.items():
            print(f"✅ {region.upper()} manager created")
            print(f"   Auth URL: {manager.auth_url}")
            print(f"   Cookie source: {manager.cookie_value[:20]}...")

        # Test 3: Verify correct cookie values per region
        print("\nTest 3: Verify region-specific cookie values")

        expected_cookies = {
            "cn": os.getenv("CAS_SESSION_cn"),
            "i18n": os.getenv("CAS_SESSION_i18n"),
            "us": os.getenv("CAS_SESSION_us")
        }

        for region, expected_cookie in expected_cookies.items():
            manager = jwt_managers[region]
            if manager.cookie_value == expected_cookie:
                print(f"✅ {region.upper()}: Correct cookie value")
            else:
                print(f"❌ {region.upper()}: Cookie mismatch")

        # Test 4: Test explicit cookie override
        print("\nTest 4: Test explicit cookie override")
        explicit_cookie = "explicit_override_test_cookie"
        override_manager = JWTAuthManager(cookie_value=explicit_cookie, region="us")

        if override_manager.cookie_value == explicit_cookie:
            print(f"✅ Explicit override works correctly")
        else:
            print(f"❌ Explicit override failed")

        # Test 5: Cleanup
        print("\nTest 5: Resource cleanup")
        for manager in jwt_managers.values():
            await manager.close()
        await override_manager.close()
        print("✅ All JWT managers cleaned up successfully")

    except Exception as e:
        print(f"❌ Error during JWT manager creation: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== .env File Integration Test Completed ===")


if __name__ == "__main__":
    asyncio.run(test_dotenv_integration())