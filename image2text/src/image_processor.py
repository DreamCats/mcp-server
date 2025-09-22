"""
图片处理核心模块
负责图片验证、格式转换和文本提取
"""

import base64
import imghdr
import os
import re
from pathlib import Path
from typing import Optional, Tuple
from api_client import APIClient
from config import config


class ImageProcessor:
    """图片处理器"""

    def __init__(self, base_url: str, api_key: str, model_id: str):
        """
        初始化图片处理器

        Args:
            base_url: API基础地址
            api_key: API密钥
            model_id: 模型ID
        """
        self.api_client = APIClient(base_url, api_key, model_id)

    def _is_base64(self, data: str) -> bool:
        """
        判断是否为base64编码数据

        Args:
            data: 待检测的字符串

        Returns:
            是否为base64编码
        """
        # 用户输入的 base64，可能会带有data:image/png;base64, 前缀
        if data.startswith('data:'):
            parts = data.split(',', 1)
            if len(parts) == 2:
                data = parts[1]
            else:
                return False

        # base64编码的基本特征：只包含特定字符，长度是4的倍数
        if not data or len(data) % 4 != 0:
            return False

        # 检查是否只包含base64允许的字符
        base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
        return bool(base64_pattern.match(data))

    def _is_file_path(self, data: str) -> bool:
        """
        判断是否为文件路径

        Args:
            data: 待检测的字符串

        Returns:
            是否为文件路径
        """
        # 检查是否为文件路径（包含路径分隔符或文件扩展名）
        if not data or len(data) > 1024:  # 限制路径长度
            return False

        # 检查是否包含路径特征
        has_path_separators = '/' in data or '\\' in data
        has_file_extension = '.' in data and len(data.split('.')[-1]) <= 10

        # 检查是否为绝对路径或相对路径
        is_absolute_path = data.startswith('/') or (len(data) > 2 and data[1] == ':')
        is_relative_path = data.startswith('./') or data.startswith('../')

        return has_path_separators or has_file_extension or is_absolute_path or is_relative_path

    def _read_image_file(self, file_path: str) -> str:
        """
        读取图片文件并转换为base64编码

        Args:
            file_path: 图片文件路径

        Returns:
            base64编码的图片数据

        Raises:
            ValueError: 文件不存在或读取失败
        """
        try:
            # 检查文件是否存在
            path = Path(file_path)
            if not path.exists():
                raise ValueError(f"文件不存在: {file_path}")

            if not path.is_file():
                raise ValueError(f"路径不是文件: {file_path}")

            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > config.MAX_IMAGE_SIZE:
                raise ValueError(f"图片文件超过大小限制: {file_size} > {config.MAX_IMAGE_SIZE}")

            # 读取文件内容
            with open(path, 'rb') as f:
                image_bytes = f.read()

            # 验证是否为有效图片
            image_type = imghdr.what(None, image_bytes)
            if not image_type:
                raise ValueError("无法识别的图片格式")

            mime_type = f"image/{image_type}"
            if mime_type not in config.SUPPORTED_FORMATS:
                raise ValueError(f"不支持的图片格式: {mime_type}")

            # 转换为base64
            return base64.b64encode(image_bytes).decode('utf-8')

        except (OSError, IOError) as e:
            raise ValueError(f"读取文件失败: {str(e)}")

    async def extract_text(self, image_input: str, prompt: Optional[str] = None) -> str:
        """
        从图片中提取文本内容

        Args:
            image_input: base64编码的图片数据或图片文件路径
            prompt: 可选的提示词

        Returns:
            提取的文本内容
        """
        # 判断输入类型并处理
        if self._is_base64(image_input):
            # base64编码数据
            image_data = image_input
        elif self._is_file_path(image_input):
            # 文件路径，读取并转换为base64
            image_data = self._read_image_file(image_input)
        else:
            raise ValueError("输入必须是base64编码的图片数据或有效的图片文件路径")

        # 验证图片格式
        if not self._validate_image(image_data):
            raise ValueError("不支持的图片格式或图片数据无效")

        # 检查图片大小
        image_size = len(base64.b64decode(image_data))
        if image_size > config.MAX_IMAGE_SIZE:
            raise ValueError(f"图片大小超过限制: {image_size} > {config.MAX_IMAGE_SIZE}")

        # 调用API进行文本提取
        prompt = prompt or "请详细描述这张图片的内容，包括文字和视觉元素"
        result = await self.api_client.vision_completion(image_data, prompt)

        return result.strip()

    def _validate_image(self, image_data: str) -> bool:
        """
        验证图片数据的有效性

        Args:
            image_data: base64编码的图片数据

        Returns:
            是否有效
        """
        try:
            # 解码base64数据
            image_bytes = base64.b64decode(image_data)

            # 检测图片格式
            image_type = imghdr.what(None, image_bytes)

            # 检查支持的格式
            if not image_type:
                return False

            mime_type = f"image/{image_type}"
            return mime_type in config.SUPPORTED_FORMATS

        except Exception:
            return False

    def _get_image_info(self, image_data: str) -> dict:
        """
        获取图片信息

        Args:
            image_data: base64编码的图片数据

        Returns:
            图片信息字典
        """
        try:
            image_bytes = base64.b64decode(image_data)
            image_type = imghdr.what(None, image_bytes)

            return {
                "format": image_type,
                "size": len(image_bytes),
                "mime_type": f"image/{image_type}" if image_type else "unknown"
            }
        except Exception:
            return {
                "format": "unknown",
                "size": 0,
                "mime_type": "unknown"
            }