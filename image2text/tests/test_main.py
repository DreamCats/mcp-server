"""
主模块单元测试
"""

import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from src.main import extract_text_from_image, analyze_image_content, get_supported_formats


class TestMainModule:
    """测试主模块功能"""

    @pytest.fixture
    def valid_base64_image(self):
        """创建有效的base64图片数据"""
        # 创建一个1x1像素的PNG图片数据
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd4c\x00\x00\x00\x00IEND\xaeB`\x82'
        return base64.b64encode(png_data).decode('utf-8')

    @pytest.mark.asyncio
    async def test_extract_text_success(self, valid_base64_image):
        """测试成功的文本提取"""
        with patch('src.main.ImageProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.extract_text.return_value = "这是一张测试图片"
            mock_processor_class.return_value = mock_processor

            result = await extract_text_from_image(valid_base64_image)

            assert result == "这是一张测试图片"
            mock_processor.extract_text.assert_called_once_with(
                valid_base64_image,
                "请详细描述这张图片的内容，包括文字和视觉元素"
            )

    @pytest.mark.asyncio
    async def test_extract_text_with_custom_params(self, valid_base64_image):
        """测试自定义参数的文本提取"""
        with patch('src.main.ImageProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.extract_text.return_value = "自定义结果"
            mock_processor_class.return_value = mock_processor

            result = await extract_text_from_image(
                image_data=valid_base64_image,
                api_base_url="https://custom.api.com",
                api_key="custom_key",
                model_id="custom_model",
                prompt="自定义提示词"
            )

            assert result == "自定义结果"
            mock_processor_class.assert_called_once_with(
                base_url="https://custom.api.com",
                api_key="custom_key",
                model_id="custom_model"
            )
            mock_processor.extract_text.assert_called_once_with(
                valid_base64_image,
                "自定义提示词"
            )

    @pytest.mark.asyncio
    async def test_extract_text_error_handling(self, valid_base64_image):
        """测试错误处理"""
        with patch('src.main.ImageProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.extract_text.side_effect = ValueError("无效的图片格式")
            mock_processor_class.return_value = mock_processor

            result = await extract_text_from_image(valid_base64_image)

            assert "参数错误: 无效的图片格式" in result

    @pytest.mark.asyncio
    async def test_analyze_image_general(self, valid_base64_image):
        """测试通用图片分析"""
        with patch('src.main.extract_text_from_image', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "这是一张风景照片"

            result = await analyze_image_content(
                image_data=valid_base64_image,
                analysis_type="general"
            )

            assert result == "这是一张风景照片"
            mock_extract.assert_called_once()

            # 验证调用的参数
            call_args = mock_extract.call_args
            assert call_args[1]["prompt"] == "请详细描述这张图片的内容，包括主要元素、场景和氛围"

    @pytest.mark.asyncio
    async def test_analyze_image_text(self, valid_base64_image):
        """测试文本分析"""
        with patch('src.main.extract_text_from_image', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "图片中的文字内容"

            result = await analyze_image_content(
                image_data=valid_base64_image,
                analysis_type="text"
            )

            assert result == "图片中的文字内容"
            mock_extract.assert_called_once()

            # 验证调用的参数
            call_args = mock_extract.call_args
            assert call_args[1]["prompt"] == "请提取图片中的所有文字内容，保持原有格式"

    @pytest.mark.asyncio
    async def test_analyze_image_objects(self, valid_base64_image):
        """测试物体识别"""
        with patch('src.main.extract_text_from_image', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "识别到的物体列表"

            result = await analyze_image_content(
                image_data=valid_base64_image,
                analysis_type="objects"
            )

            assert result == "识别到的物体列表"
            mock_extract.assert_called_once()

            # 验证调用的参数
            call_args = mock_extract.call_args
            assert call_args[1]["prompt"] == "请识别并列出图片中的所有物体及其位置"

    @pytest.mark.asyncio
    async def test_analyze_image_scene(self, valid_base64_image):
        """测试场景分析"""
        with patch('src.main.extract_text_from_image', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "场景描述信息"

            result = await analyze_image_content(
                image_data=valid_base64_image,
                analysis_type="scene"
            )

            assert result == "场景描述信息"
            mock_extract.assert_called_once()

            # 验证调用的参数
            call_args = mock_extract.call_args
            assert call_args[1]["prompt"] == "请描述图片中的场景、环境和背景信息"

    @pytest.mark.asyncio
    async def test_analyze_image_unknown_type(self, valid_base64_image):
        """测试未知的分析类型"""
        with patch('src.main.extract_text_from_image', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "默认分析结果"

            result = await analyze_image_content(
                image_data=valid_base64_image,
                analysis_type="unknown_type"
            )

            assert result == "默认分析结果"
            mock_extract.assert_called_once()

            # 验证使用了默认提示词
            call_args = mock_extract.call_args
            assert call_args[1]["prompt"] == "请详细描述这张图片的内容，包括主要元素、场景和氛围"

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """测试获取支持的格式"""
        with patch('src.main.config') as mock_config:
            mock_config.SUPPORTED_FORMATS = ["image/jpeg", "image/png"]
            mock_config.MAX_IMAGE_SIZE = 5 * 1024 * 1024

            result = await get_supported_formats()

            assert result["supported_formats"] == ["image/jpeg", "image/png"]
            assert result["max_image_size"] == 5 * 1024 * 1024
            assert result["max_image_size_mb"] == 5.0