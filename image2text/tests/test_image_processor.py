"""
图片处理器模块单元测试
"""

import pytest
import base64
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from src.image_processor import ImageProcessor
from src.config import config


class TestImageProcessor:
    """测试图片处理器"""

    @pytest.fixture
    def processor(self):
        """创建图片处理器实例"""
        return ImageProcessor(
            base_url="https://test.api.com",
            api_key="test_key",
            model_id="test_model"
        )

    @pytest.fixture
    def valid_base64_image(self):
        """创建有效的base64图片数据"""
        # 创建一个1x1像素的PNG图片数据
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd4c\x00\x00\x00\x00IEND\xaeB`\x82'
        return base64.b64encode(png_data).decode('utf-8')

    @pytest.fixture
    def invalid_base64_data(self):
        """创建无效的base64数据"""
        return "invalid_base64_string_!!!"

    @pytest.fixture
    def temp_image_file(self, valid_base64_image):
        """创建临时图片文件"""
        # 解码base64数据
        image_bytes = base64.b64decode(valid_base64_image)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_file_path = tmp_file.name

        yield tmp_file_path

        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

    @pytest.mark.asyncio
    async def test_extract_text_success(self, processor, valid_base64_image):
        """测试成功的文本提取"""
        with patch.object(processor.api_client, 'vision_completion', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = "这是一张测试图片"

            result = await processor.extract_text(valid_base64_image)

            assert result == "这是一张测试图片"
            mock_api.assert_called_once_with(valid_base64_image, "请详细描述这张图片的内容，包括文字和视觉元素")

    @pytest.mark.asyncio
    async def test_extract_text_with_custom_prompt(self, processor, valid_base64_image):
        """测试自定义提示词的文本提取"""
        custom_prompt = "请识别图片中的文字"

        with patch.object(processor.api_client, 'vision_completion', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = "图片中的文字内容"

            result = await processor.extract_text(valid_base64_image, custom_prompt)

            assert result == "图片中的文字内容"
            mock_api.assert_called_once_with(valid_base64_image, custom_prompt)

    @pytest.mark.asyncio
    async def test_extract_text_invalid_image(self, processor, invalid_base64_data):
        """测试无效图片数据"""
        with pytest.raises(ValueError, match="输入必须是base64编码的图片数据或有效的图片文件路径"):
            await processor.extract_text(invalid_base64_data)

    @pytest.mark.asyncio
    async def test_extract_text_oversized_image(self, processor, valid_base64_image):
        """测试超大图片"""
        # 创建一个超过大小限制的大图片数据，基于有效图片格式
        # 先获取有效图片的解码数据
        valid_bytes = base64.b64decode(valid_base64_image)

        # 计算需要重复多少次才能达到超过10MB的大小
        target_size = config.MAX_IMAGE_SIZE + 1024  # 稍微超过限制
        repeat_count = (target_size // len(valid_bytes)) + 1

        # 创建大图片数据
        large_bytes = valid_bytes * repeat_count
        large_data = base64.b64encode(large_bytes).decode('utf-8')

        # Mock API调用以避免实际网络请求
        with patch.object(processor.api_client, 'vision_completion', return_value="mocked result"):
            with pytest.raises(ValueError, match="图片大小超过限制.*"):
                await processor.extract_text(large_data)

    def test_validate_image_valid_png(self, processor, valid_base64_image):
        """测试有效的PNG图片验证"""
        is_valid = processor._validate_image(valid_base64_image)
        assert is_valid is True

    def test_validate_image_invalid_data(self, processor, invalid_base64_data):
        """测试无效数据的图片验证"""
        is_valid = processor._validate_image(invalid_base64_data)
        assert is_valid is False

    def test_validate_image_corrupted_data(self, processor):
        """测试损坏的图片数据验证"""
        # 创建看起来像base64但不是有效图片的数据
        corrupted_data = base64.b64encode(b'not an image').decode('utf-8')
        is_valid = processor._validate_image(corrupted_data)
        assert is_valid is False

    def test_get_image_info_valid(self, processor, valid_base64_image):
        """测试获取有效图片信息"""
        info = processor._get_image_info(valid_base64_image)

        assert info["format"] == "png"
        assert info["size"] > 0
        assert info["mime_type"] == "image/png"

    def test_get_image_info_invalid(self, processor, invalid_base64_data):
        """测试获取无效图片信息"""
        info = processor._get_image_info(invalid_base64_data)

        assert info["format"] == "unknown"
        assert info["size"] == 0
        assert info["mime_type"] == "unknown"

    def test_is_base64_valid(self, processor, valid_base64_image):
        """测试有效的base64检测"""
        assert processor._is_base64(valid_base64_image) is True

    def test_is_base64_invalid(self, processor):
        """测试无效的base64检测"""
        assert processor._is_base64("not base64!!!") is False
        assert processor._is_base64("/path/to/image.png") is False

    def test_is_file_path_valid(self, processor):
        """测试有效的文件路径检测"""
        assert processor._is_file_path("/Users/bytedance/Demo/doc/assets/test.png") is True
        assert processor._is_file_path("./images/test.jpg") is True
        assert processor._is_file_path("../assets/logo.png") is True
        assert processor._is_file_path("C:\\Users\\test\\image.jpg") is True

    def test_is_file_path_invalid(self, processor, valid_base64_image):
        """测试无效的文件路径检测"""
        assert processor._is_file_path(valid_base64_image) is False
        assert processor._is_file_path("not a path") is False

    @pytest.mark.asyncio
    async def test_extract_text_from_file_path(self, processor, temp_image_file):
        """测试从文件路径提取文本"""
        with patch.object(processor.api_client, 'vision_completion', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = "这是从文件读取的图片"

            result = await processor.extract_text(temp_image_file)

            assert result == "这是从文件读取的图片"
            # 验证调用了API，参数应该是base64编码的数据
            call_args = mock_api.call_args[0]
            assert len(call_args) == 2  # image_data和prompt
            assert processor._is_base64(call_args[0]) is True

    @pytest.mark.asyncio
    async def test_extract_text_from_nonexistent_file(self, processor):
        """测试不存在的文件路径"""
        with pytest.raises(ValueError, match="文件不存在"):
            await processor.extract_text("/nonexistent/image.png")

    @pytest.mark.asyncio
    async def test_extract_text_from_invalid_file(self, processor):
        """测试无效的文件路径"""
        # 创建临时文本文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b"this is not an image")
            tmp_file_path = tmp_file.name

        try:
            with pytest.raises(ValueError, match="无法识别的图片格式"):
                await processor.extract_text(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)

    @pytest.mark.asyncio
    async def test_extract_text_oversized_file(self, processor):
        """测试超大文件"""
        # 创建大文件
        large_content = b"x" * (config.MAX_IMAGE_SIZE + 1024)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(large_content)
            tmp_file_path = tmp_file.name

        try:
            with pytest.raises(ValueError, match="图片文件超过大小限制"):
                await processor.extract_text(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)

    @pytest.mark.asyncio
    async def test_api_client_error_handling(self, processor, valid_base64_image):
        """测试API客户端错误处理"""
        with patch.object(processor.api_client, 'vision_completion', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API调用失败")

            with pytest.raises(Exception, match="API调用失败"):
                await processor.extract_text(valid_base64_image)