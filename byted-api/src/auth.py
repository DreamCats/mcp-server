"""
JWT Authentication Module for ByteDance MCP Server

This module handles JWT token acquisition and management for ByteDance internal APIs.
"""

import os
import time
from typing import Optional
import httpx
import structlog
from pathlib import Path
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

# Load environment variables from .env file in project root
def load_env_file():
    """Load .env file from project root directory"""
    try:
        # Find project root (assuming src/auth.py structure)
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"

        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment variables from .env file", env_file=str(env_file))
        else:
            logger.warning("No .env file found in project root", project_root=str(project_root))
    except Exception as e:
        logger.error("Failed to load .env file", error=str(e))

# Load .env file when module is imported
load_env_file()


class JWTAuthManager:
    """JWT Token Manager for ByteDance Authentication with Multi-Region Support"""

    # Region-specific auth endpoints
    REGION_AUTH_URLS = {
        "cn": "https://cloud.bytedance.net/auth/api/v1/jwt",
        "i18n": "https://cloud-i18n.bytedance.net/auth/api/v1/jwt",
        "us": "https://cloud-ttp-us.bytedance.net/auth/api/v1/jwt"
    }

    def __init__(self, cookie_value: Optional[str] = None, region: str = "cn"):
        """
        Initialize JWT Auth Manager

        Args:
            cookie_value: CAS_SESSION cookie value, defaults to region-specific env var
            region: Region identifier ("cn", "i18n", "us"), defaults to "cn"
        """
        # Use region-specific cookie value if not provided
        if cookie_value:
            self.cookie_value = cookie_value
        else:
            # Try region-specific environment variable first
            region_cookie_var = f"CAS_SESSION_{region}"
            self.cookie_value = os.getenv(region_cookie_var)

            # Fallback to generic CAS_SESSION if region-specific not found
            if not self.cookie_value:
                self.cookie_value = os.getenv("CAS_SESSION")

        if not self.cookie_value:
            raise ValueError(f"CAS_SESSION cookie value is required for region {region}. "
                           f"Please set {region_cookie_var} or CAS_SESSION environment variable")

        self.region = region
        self.jwt_token: Optional[str] = None
        self.expires_at: Optional[float] = None
        self.auth_url = self.REGION_AUTH_URLS.get(region, self.REGION_AUTH_URLS["cn"])

        # HTTP client with proper timeout and headers
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br, zstd",
            }
        )

    async def get_jwt_token(self, force_refresh: bool = False) -> str:
        """
        Get JWT token, refresh if necessary

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            JWT token string

        Raises:
            RuntimeError: If token acquisition fails
        """
        if not force_refresh and self.is_token_valid():
            logger.debug("Using cached JWT token")
            return self.jwt_token

        logger.info("Acquiring new JWT token")

        try:
            headers = {
                "Cookie": f"CAS_SESSION={self.cookie_value}"
            }

            response = await self.client.get(self.auth_url, headers=headers)
            response.raise_for_status()

            # JWT token is in response headers
            self.jwt_token = response.headers.get("x-jwt-token")
            if not self.jwt_token:
                raise RuntimeError("No JWT token in response headers")

            # Set expiration time (assuming 1 hour validity)
            self.expires_at = time.time() + 3600

            logger.info("JWT token acquired successfully")
            return self.jwt_token

        except httpx.HTTPError as e:
            logger.error("HTTP error acquiring JWT token", error=str(e))
            raise RuntimeError(f"Failed to acquire JWT token: {e}")
        except Exception as e:
            logger.error("Unexpected error acquiring JWT token", error=str(e))
            raise RuntimeError(f"Unexpected error: {e}")

    def is_token_valid(self) -> bool:
        """
        Check if current token is valid

        Returns:
            True if token exists and is not expired
        """
        if not self.jwt_token or not self.expires_at:
            return False

        # Check if token expires in less than 5 minutes
        return time.time() < (self.expires_at - 300)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            # Note: This is a fallback, proper cleanup should use close()
            if hasattr(self, 'client'):
                import asyncio
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.client.aclose())
        except Exception:
            pass