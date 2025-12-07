"""
Create nested blocks module

This module implements functionality to create nested blocks in documents via Lark API.
"""

import httpx
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class CreateBlock:
    """
    Tool class for creating nested blocks in documents
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_nested_blocks(
        self,
        document_id: str,
        block_id: str,
        children_id: List[str],
        descendants: List[Dict[str, Any]],
        index: int = 0,
        document_revision_id: int = -1,
        client_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create nested blocks in a document

        Args:
            document_id: Document ID where blocks will be created
            block_id: Parent block ID (use empty string for root level)
            children_id: List of child block IDs to insert
            descendants: List of descendant block objects with their properties
            index: Insertion index (default: 0)
            document_revision_id: Document revision ID (default: -1 for latest)
            client_token: Optional UUIDv4 for idempotent updates

        Returns:
            Dictionary containing:
            - block_id_relations: List of temporary to actual block ID mappings
            - children: List of created child blocks
            - client_token: Operation identifier
            - document_revision_id: New document revision ID

        Raises:
            ValueError: When authentication headers are missing
            RuntimeError: When API call fails
        """
        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to create nested blocks
        # 父块的block_id，表示为其创建一批子块。如果需要对文档树根节点创建子块，可将 document_id 填入此处。你可调用获取文档所有块获取文档中块的 block_id。
        if block_id == "":
            block_id = document_id

        api_url = f"https://open.larkoffice.com/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/descendant"
        

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Build query parameters
        params = {
            "document_revision_id": str(document_revision_id)
        }
        if client_token:
            params["client_token"] = client_token

        # Build request body
        request_body = {
            "index": index,
            "children_id": children_id,
            "descendants": descendants
        }

        response = await self.client.post(
            api_url, 
            params=params, 
            json=request_body, 
            headers=request_headers
        )

        # logger.info("create_nested_blocks", status_code=response.status_code, response=response.json())

        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {})

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()