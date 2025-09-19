"""
JWT Authentication Module for ByteDance MCP Server

This module handles JWT token acquisition and management for ByteDance internal APIs.
"""

import os
import time
from typing import Optional
import httpx
import structlog

logger = structlog.get_logger(__name__)


class JWTAuthManager:
    """JWT Token Manager for ByteDance Authentication"""

    def __init__(self, cookie_value: Optional[str] = None):
        """
        Initialize JWT Auth Manager

        Args:
            cookie_value: CAS_SESSION cookie value, defaults to env var CAS_SESSION
        """
        self.cookie_value = cookie_value or os.getenv("CAS_SESSION")
        if not self.cookie_value:
            raise ValueError("CAS_SESSION cookie value is required")

        self.jwt_token: Optional[str] = None
        self.expires_at: Optional[float] = None
        self.auth_url = "https://cloud.bytedance.net/auth/api/v1/jwt"

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