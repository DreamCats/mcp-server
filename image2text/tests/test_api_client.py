"""
API客户端模块单元测试
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from src.api_client import APIClient


class TestAPIClient:
    """测试API客户端"""

    @pytest.fixture
    def api_client(self):
        """创建API客户端实例"""
        return APIClient(
            base_url="https://test.api.com",
            api_key="test_key",
            model_id="test_model"
        )

    @pytest.mark.asyncio
    async def test_successful_vision_completion(self, api_client):
        """测试成功的视觉理解调用"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "这是一张测试图片"
                }
            }]
        }

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await api_client.vision_completion(
                image_data="test_base64_data",
                prompt="描述这张图片"
            )

            assert result == "这是一张测试图片"
            mock_post.assert_called_once()

            # 验证调用参数
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://test.api.com/chat/completions"
            payload = call_args[1]["json"]
            assert payload["model"] == "test_model"
            assert payload["messages"][0]["content"][0]["text"] == "描述这张图片"

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, api_client):
        """测试无效的API密钥"""
        mock_response = MagicMock()
        mock_response.status_code = 401

        http_error = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = http_error

            with pytest.raises(Exception, match="API密钥无效"):
                await api_client.vision_completion("test_data")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, api_client):
        """测试频率限制错误"""
        mock_response = MagicMock()
        mock_response.status_code = 429

        http_error = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = http_error

            with pytest.raises(Exception, match="API调用频率超限"):
                await api_client.vision_completion("test_data")

    @pytest.mark.asyncio
    async def test_network_error(self, api_client):
        """测试网络错误"""
        network_error = httpx.RequestError("Network error")

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = network_error

            with pytest.raises(Exception, match="网络请求失败"):
                await api_client.vision_completion("test_data")

    @pytest.mark.asyncio
    async def test_invalid_response_format(self, api_client):
        """测试无效的响应格式"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invalid": "format"  # 缺少choices字段
        }

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="API返回格式无效"):
                await api_client.vision_completion("test_data")

    @pytest.mark.asyncio
    async def test_empty_choices(self, api_client):
        """测试空的choices数组"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": []  # 空数组
        }

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="API返回格式无效"):
                await api_client.vision_completion("test_data")

    @pytest.mark.asyncio
    async def test_client_close(self, api_client):
        """测试客户端关闭"""
        with patch.object(api_client.client, 'aclose', new_callable=AsyncMock) as mock_close:
            await api_client.close()
            mock_close.assert_called_once()

    def test_client_initialization(self):
        """测试客户端初始化"""
        client = APIClient(
            base_url="https://api.example.com/",
            api_key="test_key_123",
            model_id="gpt-4-vision"
        )

        assert client.base_url == "https://api.example.com"
        assert client.api_key == "test_key_123"
        assert client.model_id == "gpt-4-vision"
        assert client.client.timeout.connect == 30  # 默认超时时间