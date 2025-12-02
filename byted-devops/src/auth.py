"""
字节跳动 MCP 服务器 JWT 认证模块

本模块处理字节跳动内部 API 的 JWT 令牌获取和管理，支持多区域认证配置。
提供基于 Cookie 的 JWT 认证功能，支持自动令牌刷新和过期检测。
"""

import os
import time
from typing import Optional
import httpx
import structlog
from pathlib import Path
from dotenv import load_dotenv

# 获取日志记录器实例
logger = structlog.get_logger(__name__)



class JWTAuthManager:
    """
    JWT 认证管理器

    提供字节跳动内部 API 的 JWT 令牌管理功能，支持多区域认证配置。
    该类负责获取、缓存和刷新 JWT 令牌，支持基于 Cookie 的认证方式。
    """

    auth_url = "https://cloud.bytedance.net/auth/api/v1/jwt"


    def __init__(self, cookie_value: Optional[str] = None):
        """
        初始化 JWT 认证管理器

        根据提供的 Cookie 值和区域标识符初始化认证管理器。
        如果没有提供 Cookie 值，会尝试从环境变量中获取。

        参数:
            cookie_value: CAS_SESSION Cookie 值，如果为 None 则使用区域特定的环境变量
        异常:
            ValueError: 如果无法获取到有效的 Cookie 值
        """
        
        # 使用提供的 Cookie 值
        if cookie_value:
            self.cookie_value = cookie_value
            

        # 验证 Cookie 值是否存在
        if not self.cookie_value:
            raise ValueError(f"需要 CAS_SESSION Cookie 值。"
                           f"请设置 CAS_SESSION 环境变量")

        # 初始化属性
        self.jwt_token: Optional[str] = None  # JWT 令牌
        self.expires_at: Optional[float] = None  # 令牌过期时间

        # 配置 HTTP 客户端
        # 设置合适的超时时间和请求头，模拟浏览器行为
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30秒超时
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br, zstd",
            }
        )

    async def get_jwt_token(self, force_refresh: bool = False) -> str:
        """
        获取 JWT 令牌，必要时进行刷新

        如果当前令牌有效且未强制刷新，则返回缓存的令牌。
        否则，向认证服务请求新的 JWT 令牌。

        参数:
            force_refresh: 即使当前令牌有效也强制刷新

        返回:
            JWT 令牌字符串

        异常:
            RuntimeError: 如果令牌获取失败
        """
        # 如果令牌有效且未强制刷新，使用缓存的令牌
        if not force_refresh and self.is_token_valid():
            logger.debug("使用缓存的 JWT 令牌")
            return self.jwt_token

        logger.info("正在获取新的 JWT 令牌")

        try:
            # 准备认证请求头，包含 Cookie 信息
            headers = {
                "Cookie": f"CAS_SESSION={self.cookie_value}"
            }

            # 发送 GET 请求到认证服务
            response = await self.client.get(self.auth_url, headers=headers)
            response.raise_for_status()  # 检查 HTTP 状态码

            # JWT 令牌在响应头中
            self.jwt_token = response.headers.get("x-jwt-token")
            if not self.jwt_token:
                raise RuntimeError("响应头中没有 JWT 令牌")

            # 设置过期时间（假设令牌有效期为 1 小时）
            self.expires_at = time.time() + 3600

            logger.info("JWT 令牌获取成功")
            return self.jwt_token

        except httpx.HTTPError as e:
            # 处理 HTTP 错误
            logger.error("获取 JWT 令牌时发生 HTTP 错误", error=str(e))
            raise RuntimeError(f"获取 JWT 令牌失败: {e}")
        except Exception as e:
            # 处理其他异常
            logger.error("获取 JWT 令牌时发生意外错误", error=str(e))
            raise RuntimeError(f"意外错误: {e}")

    def is_token_valid(self) -> bool:
        """
        检查当前令牌是否有效

        验证令牌是否存在且未过期。如果令牌将在 5 分钟内过期，也视为无效。

        返回:
            如果令牌存在且未过期返回 True，否则返回 False
        """
        # 检查令牌和过期时间是否存在
        if not self.jwt_token or not self.expires_at:
            return False

        # 检查令牌是否在 5 分钟内过期
        # 如果令牌将在 5 分钟内过期，提前刷新以避免使用过期令牌
        return time.time() < (self.expires_at - 300)

    async def close(self):
        """
        关闭 HTTP 客户端

        关闭 HTTP 客户端连接，释放资源。
        """
        await self.client.aclose()

    def __del__(self):
        """
        对象销毁时的清理工作

        在对象被垃圾回收时尝试关闭 HTTP 客户端连接。
        注意：这是后备方案，正确的清理应该使用 close() 方法。
        """
        try:
            # 检查是否存在客户端属性
            if hasattr(self, 'client'):
                import asyncio
                # 如果事件循环正在运行，则异步关闭客户端
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.client.aclose())
        except Exception:
            # 忽略清理过程中的任何异常
            pass