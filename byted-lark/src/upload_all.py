"""
Upload media files module

This module implements functionality to upload media files via Lark API.
"""

import httpx
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class UploadAll:
    """
    Tool class for uploading media files
    """

    def __init__(self, auth_manager):
        """
        Initialize with auth manager instance

        Args:
            auth_manager: TenantAccessTokenAuthManager instance for handling authentication
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def upload_media(
        self,
        file_name: str,
        parent_type: str,
        parent_node: str,
        file_content: bytes,
        size: int,
        checksum: Optional[str] = None,
        extra: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload media file

        Args:
            file_name: Name of the file to upload (max 250 characters)
            parent_type: Upload point type, options: doc_image/docx_image/sheet_image/doc_file/docx_file
            parent_node: Upload point token (target cloud document token)
            file_content: Binary content of the file
            size: File size in bytes (max 20,971,520 bytes)
            checksum: Optional Adler-32 checksum of the file
            extra: Optional extra info in format: {"drive_route_token":"document token"}

        Returns:
            Dictionary containing:
            - file_token: Token of the uploaded file

        Raises:
            ValueError: When authentication headers are missing or invalid parameters
            RuntimeError: When API call fails
        """
        # Validate parent_type
        valid_parent_types = [
            "doc_image", "docx_image", "sheet_image", 
            "doc_file", "docx_file"
        ]
        if parent_type not in valid_parent_types:
            raise ValueError(f"parent_type must be one of: {', '.join(valid_parent_types)}")

        # Validate file size
        if size > 20971520:  # 20MB limit
            raise ValueError("File size exceeds maximum limit of 20MB")

        # Get tenant_access_token through auth manager
        tenant_access_token = await self.auth.get_tenant_access_token()

        # Call API to upload file
        api_url = "https://open.larkoffice.com/open-apis/drive/v1/medias/upload_all"

        request_headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "multipart/form-data; boundary=---7MA4YWxkTrZu0gW"
        }

        # Build multipart form data
        files = {
            "file": (file_name, file_content)
        }

        # Build form fields
        data = {
            "file_name": file_name,
            "parent_type": parent_type,
            "parent_node": parent_node,
            "size": str(size)
        }
        
        if checksum:
            data["checksum"] = checksum
        if extra:
            data["extra"] = extra

        response = await self.client.post(
            api_url, 
            files=files, 
            data=data, 
            headers=request_headers
        )

        logger.info("upload_media", status_code=response.status_code, response=response.json())

        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API call failed: {result.get('msg')}")

        return result.get("data", {})

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()