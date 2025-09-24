"""
Test script for region-specific JWT authentication with different cookie values
"""

import os
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth import JWTAuthManager


async def test_region_specific_cookies():
    """Test region-specific cookie value resolution"""
    print("=== Testing Region-Specific Cookie Values ===\n")

    # Test 1: Default behavior (no env vars set)
    print("Test 1: Default behavior (fallback to generic CAS_SESSION)")
    try:
        # Temporarily set a generic CAS_SESSION for testing
        original_cas_session = os.getenv("CAS_SESSION")
        os.environ["CAS_SESSION"] = "generic_test_cookie"

        auth_manager = JWTAuthManager(region="cn")
        print(f"✅ CN region - Cookie: {auth_manager.cookie_value[:20]}...")
        print(f"   Auth URL: {auth_manager.auth_url}")

        # Clean up
        if original_cas_session:
            os.environ["CAS_SESSION"] = original_cas_session
        else:
            del os.environ["CAS_SESSION"]

    except Exception as e:
        print(f"❌ CN region failed: {e}")

    # Test 2: Region-specific cookies
    print("\nTest 2: Region-specific cookie values")

    # Set up test environment variables
    test_cookies = {
        "CAS_SESSION_cn": "cn_test_cookie_value",
        "CAS_SESSION_i18n": "i18n_test_cookie_value",
        "CAS_SESSION_us": "us_test_cookie_value"
    }

    # Store original values to restore later
    original_values = {}
    for key, value in test_cookies.items():
        original_values[key] = os.getenv(key)
        os.environ[key] = value

    try:
        # Test each region
        regions = ["cn", "i18n", "us"]
        expected_cookies = {
            "cn": "cn_test_cookie_value",
            "i18n": "i18n_test_cookie_value",
            "us": "us_test_cookie_value"
        }

        for region in regions:
            try:
                auth_manager = JWTAuthManager(region=region)
                expected_cookie = expected_cookies[region]

                if auth_manager.cookie_value == expected_cookie:
                    print(f"✅ {region.upper()} region - Correct cookie: {auth_manager.cookie_value[:20]}...")
                else:
                    print(f"❌ {region.upper()} region - Expected: {expected_cookie[:20]}..., Got: {auth_manager.cookie_value[:20]}...")

                print(f"   Auth URL: {auth_manager.auth_url}")

            except Exception as e:
                print(f"❌ {region.upper()} region failed: {e}")

    finally:
        # Restore original environment variables
        for key, original_value in original_values.items():
            if original_value is not None:
                os.environ[key] = original_value
            elif key in os.environ:
                del os.environ[key]

    # Test 3: Explicit cookie value override
    print("\nTest 3: Explicit cookie value override")
    try:
        explicit_cookie = "explicit_override_cookie"
        auth_manager = JWTAuthManager(cookie_value=explicit_cookie, region="us")

        if auth_manager.cookie_value == explicit_cookie:
            print(f"✅ Explicit override works: {auth_manager.cookie_value[:20]}...")
        else:
            print(f"❌ Explicit override failed")

    except Exception as e:
        print(f"❌ Explicit override test failed: {e}")

    # Test 4: Missing cookie error handling
    print("\nTest 4: Missing cookie error handling")

    # Clear all cookie environment variables temporarily
    cookie_vars = ["CAS_SESSION", "CAS_SESSION_cn", "CAS_SESSION_i18n", "CAS_SESSION_us"]
    cleared_vars = {}

    for var in cookie_vars:
        if var in os.environ:
            cleared_vars[var] = os.environ[var]
            del os.environ[var]

    try:
        auth_manager = JWTAuthManager(region="i18n")
        print(f"❌ Should have failed but didn't")
    except ValueError as e:
        print(f"✅ Correctly raised error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Restore cleared variables
    for var, value in cleared_vars.items():
        os.environ[var] = value

    print("\n=== Region-specific cookie test completed! ===")


if __name__ == "__main__":
    asyncio.run(test_region_specific_cookies())