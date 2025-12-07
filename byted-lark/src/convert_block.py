"""
Convert content to document blocks module

This module implements functionality to convert Markdown/HTML content to document blocks via Lark API.
"""

import httpx
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


class ConvertBlock:
    """
    Tool class for converting content to document blocks
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def convert_content_to_blocks(
        self,
        content: str,
        content_type: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Convert Markdown/HTML content to document blocks

        Args:
            content: Markdown or HTML format content to convert
            content_type: Content type, supports "markdown" or "html"

        Returns:
            Dictionary containing:
            - first_level_block_ids: List of first level block IDs
            - blocks: List of converted block objects
            - block_id_to_image_urls: List of block ID to image URL mappings

        Raises:
            ValueError: When authentication headers are missing or invalid content_type
            RuntimeError: When API call fails
        """
        if content_type not in ["markdown", "html"]:
            raise ValueError("content_type must be 'markdown' or 'html'")

        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to convert content to blocks
        api_url = "https://open.larkoffice.com/open-apis/docx/v1/documents/blocks/convert"

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        request_body = {
            "content_type": content_type,
            "content": content
        }

        response = await self.client.post(api_url, json=request_body, headers=request_headers)

        # logger.info("convert_content_to_blocks", status_code=response.status_code, response=response.json())

        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {})

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()