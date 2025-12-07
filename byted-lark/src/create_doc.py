"""
Create document module

This module implements functionality to create documents via Lark API.
"""

import httpx
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class CreateDoc:
    """
    Tool class for creating documents
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_document(
        self,
        folder_token: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new document

        Args:
            folder_token: Optional folder token where the document should be created
            title: Optional document title (1-800 characters, plain text only)

        Returns:
            Dictionary containing document information:
            - document_id: The created document ID
            - revision_id: The document revision ID
            - title: The document title

        Raises:
            ValueError: When authentication headers are missing
            RuntimeError: When API call fails
        """
        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to create document
        api_url = "https://open.larkoffice.com/open-apis/docx/v1/documents"

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Build request body
        request_body = {}
        if folder_token:
            request_body["folder_token"] = folder_token
        if title:
            request_body["title"] = title

        response = await self.client.post(api_url, json=request_body, headers=request_headers)

        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {}).get("document", {})

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()