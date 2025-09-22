"""
配置管理模块
处理API配置和环境变量
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Config(BaseSettings):
    """配置类，支持环境变量和默认值"""

    # API配置
    DEFAULT_API_BASE: str = Field(
        default="https://api.openai.com/v1",
        description="默认API基础地址"
    )
    DEFAULT_API_KEY: Optional[str] = Field(
        default=None,
        description="默认API密钥"
    )
    DEFAULT_MODEL_ID: str = Field(
        default="gpt-4-vision-preview",
        description="默认模型ID"
    )

    # 服务器配置
    SERVER_PORT: int = Field(
        default=8201,
        description="服务器端口"
    )
    SERVER_HOST: str = Field(
        default="0.0.0.0",
        description="服务器主机地址"
    )

    # 图片处理配置
    MAX_IMAGE_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="最大图片大小（字节）"
    )
    SUPPORTED_FORMATS: list = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        description="支持的图片格式"
    )

    # 请求配置
    REQUEST_TIMEOUT: int = Field(
        default=30,
        description="API请求超时时间（秒）"
    )
    MAX_RETRIES: int = Field(
        default=3,
        description="最大重试次数"
    )

    model_config = ConfigDict(
        env_file = ".env",
        case_sensitive = True,
        env_prefix = "IMAGE2TEXT_"  # 环境变量前缀
    )


# 全局配置实例
config = Config()