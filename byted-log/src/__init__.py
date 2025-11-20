"""
Initialization module for the ByteDance Live Promotion MCP server.
"""

from .auth import JWTAuthManager

__all__ = [
    "JWTAuthManager",
]