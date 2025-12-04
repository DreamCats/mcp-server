"""
Get knowledge space node information module

This module implements functionality to get knowledge space node information via Lark API.
"""

import httpx
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class GetNote:
    """
    Tool class for getting knowledge space node information
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_knowledge_space_node(
        self,
        token: str,
        obj_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get knowledge space node information

        Args:
            token: Knowledge space node token
            obj_type: Knowledge space node type, optional values: doc, docx, sheet, mindnote, bitable, wiki

        Returns:
            Node information dictionary
        """
        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to get node information
        api_url = "https://open.larkoffice.com/open-apis/wiki/v2/spaces/get_node"
        params = {"token": token}
        if obj_type:
            params["obj_type"] = obj_type

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        response = await self.client.get(api_url, params=params, headers=request_headers)
        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {}).get("node", {})

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()