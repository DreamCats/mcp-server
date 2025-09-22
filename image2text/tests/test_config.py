"""
配置管理模块单元测试
"""

import os
import pytest
from unittest.mock import patch
from src.config import Config, config


class TestConfig:
    """测试配置类"""

    def test_default_values(self):
        """测试默认值"""
        assert config.DEFAULT_API_BASE == "https://ark-cn-beijing.bytedance.net/api/v3"
        assert config.DEFAULT_MODEL_ID == "ep-20250806170811-dd4nz"
        assert config.SERVER_PORT == 8201
        assert config.SERVER_HOST == "0.0.0.0"
        assert config.MAX_IMAGE_SIZE == 10 * 1024 * 1024
        assert "image/jpeg" in config.SUPPORTED_FORMATS

    def test_environment_variables(self):
        """测试环境变量覆盖"""
        env_vars = {
            "IMAGE2TEXT_DEFAULT_API_BASE": "https://custom.api.com",
            "IMAGE2TEXT_DEFAULT_API_KEY": "test_key",
            "IMAGE2TEXT_SERVER_PORT": "8080",
            "IMAGE2TEXT_MAX_IMAGE_SIZE": "5242880"  # 5MB
        }

        with patch.dict(os.environ, env_vars):
            test_config = Config()
            assert test_config.DEFAULT_API_BASE == "https://custom.api.com"
            assert test_config.DEFAULT_API_KEY == "test_key"
            assert test_config.SERVER_PORT == 8080
            assert test_config.MAX_IMAGE_SIZE == 5242880

    def test_supported_formats(self):
        """测试支持的格式"""
        expected_formats = ["image/jpeg", "image/png", "image/webp"]
        assert config.SUPPORTED_FORMATS == expected_formats

    def test_request_config(self):
        """测试请求配置"""
        assert config.REQUEST_TIMEOUT == 30
        assert config.MAX_RETRIES == 3