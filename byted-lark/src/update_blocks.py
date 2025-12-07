"""
Batch update blocks module

This module implements functionality to batch update document blocks via Lark API.
"""

import httpx
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class UpdateBlocks:
    """
    Tool class for batch updating document blocks
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def batch_update_blocks(
        self,
        document_id: str,
        requests: List[Dict[str, Any]],
        document_revision_id: int = -1,
        client_token: Optional[str] = None,
        user_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """
        Batch update document blocks

        Args:
            document_id: Document ID where blocks will be updated
            requests: List of update requests for blocks
            document_revision_id: Document revision ID (-1 for latest version)
            client_token: Optional UUIDv4 for idempotent updates
            user_id_type: User ID type (open_id, union_id, user_id)

        Returns:
            Dictionary containing:
            - blocks: List of updated block objects
            - client_token: Operation identifier
            - document_revision_id: New document revision ID

        Raises:
            ValueError: When authentication headers are missing or invalid parameters
            RuntimeError: When API call fails
        """
        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to batch update blocks
        api_url = f"https://open.larkoffice.com/open-apis/docx/v1/documents/{document_id}/blocks/batch_update"

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Build query parameters
        params = {
            "document_revision_id": str(document_revision_id),
            "user_id_type": user_id_type
        }
        if client_token:
            params["client_token"] = client_token

        # Build request body
        request_body = {
            "requests": requests
        }

        response = await self.client.patch(
            api_url, 
            params=params, 
            json=request_body, 
            headers=request_headers
        )
        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {})

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()