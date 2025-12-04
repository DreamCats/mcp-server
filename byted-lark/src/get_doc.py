"""
Get document raw content module

This module implements functionality to get document raw content via Lark API.
"""

import httpx
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class GetDoc:
    """
    Tool class for getting document raw content
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_document_raw_content(self, document_id: str) -> str:
        """
        Get document raw content

        Args:
            document_id: Document ID (can be docx token or obj_token)

        Returns:
            Raw text content of the document
        """
        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to get document content
        api_url = f"https://open.larkoffice.com/open-apis/docx/v1/documents/{document_id}/raw_content"

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        response = await self.client.get(api_url, headers=request_headers)
        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {}).get("content", "")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()