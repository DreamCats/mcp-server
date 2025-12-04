"""
字节跳动 Lark MCP 服务器 tenant_access_token 获取模块

本模块处理字节跳动内部 API 的 tenant_access_token 获取和管理，支持多区域认证配置。
提供基于 app_id 和 app_secret 的 tenant_access_token 认证功能，支持自动令牌刷新和过期检测。
"""

import os
import time
from typing import Optional
import httpx
import structlog
from pathlib import Path
from dotenv import load_dotenv
from fastmcp.server.dependencies import get_http_headers

# 获取日志记录器实例
logger = structlog.get_logger(__name__)



class TenantAccessTokenAuthManager:
    """
    tenant_access_token 认证管理器

    提供字节跳动内部 API 的 tenant_access_token 管理功能，支持多区域认证配置。
    该类负责获取、缓存和刷新 tenant_access_token，支持基于 Cookie 的认证方式。
    """

    auth_url = "https://open.larkoffice.com/open-apis/auth/v3/tenant_access_token/internal"


    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None, use_headers: bool = False):
        """
        初始化 tenant_access_token 认证管理器

        根据提供的 app_id 和 app_secret 值初始化 tenant_access_token 认证管理器。
        如果没有提供 app_id 和 app_secret 值，会尝试从环境变量中获取。

        参数:
            app_id: 字节跳动 Lark 应用 ID，如果为 None 则使用环境变量 APP_ID 或从 headers 获取
            app_secret: 字节跳动 Lark 应用密钥，如果为 None 则使用环境变量 APP_SECRET 或从 headers 获取
            use_headers: 是否从 HTTP headers 中获取认证信息
        异常:
            ValueError: 如果无法获取到有效的 app_id 和 app_secret 值
        """
        self.use_headers = use_headers

        if use_headers:
            # 从 headers 获取认证信息
            self.app_id = None
            self.app_secret = None
        else:
            # 使用提供的 app_id 和 app_secret 值或环境变量
            self.app_id = app_id or os.getenv("APP_ID")
            self.app_secret = app_secret or os.getenv("APP_SECRET")

            # 验证 app_id 和 app_secret 值是否存在
            if not self.app_id or not self.app_secret:
                raise ValueError(f"需要 APP_ID 和 APP_SECRET 值。"
                               f"请设置 APP_ID 和 APP_SECRET 环境变量")

        # 初始化属性
        self.tenant_access_token: Optional[str] = None  # tenant_access_token 令牌
        self.expires_at: Optional[float] = None  # 令牌过期时间

        # 配置 HTTP 客户端
        # 设置合适的超时时间和请求头，模拟浏览器行为
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30秒超时
        )



    async def get_tenant_access_token(self, force_refresh: bool = False) -> str:
        """
        获取 tenant_access_token 令牌，必要时进行刷新

        如果当前令牌有效且未强制刷新，则返回缓存的令牌。
        否则，向认证服务请求新的 JWT 令牌。

        参数:
            force_refresh: 即使当前令牌有效也强制刷新

        返回:
            tenant_access_token 令牌字符串

        异常:
            RuntimeError: 如果令牌获取失败
        """
        # 如果令牌有效且未强制刷新，使用缓存的令牌
        if not force_refresh and self.is_token_valid():
            logger.debug("使用缓存的 tenant_access_token 令牌")
            return self.tenant_access_token

        logger.info("正在获取新的 tenant_access_token 令牌")

        # 获取 app_id 和 app_secret
        app_id, app_secret = self._get_credentials()

        try:
            # 发送 GET 请求到认证服务
            response = await self.client.post(self.auth_url, json={
                "app_id": app_id,
                "app_secret": app_secret
            })
            response.raise_for_status()  # 检查 HTTP 状态码

            # tenant_access_token 令牌在响应体中
            self.tenant_access_token = response.json().get("tenant_access_token")
            if not self.tenant_access_token:
                raise RuntimeError("响应体中没有 tenant_access_token 令牌")

            expire = response.json().get("expire")
            if not expire:
                raise RuntimeError("响应体中没有 expire 字段")

            # 设置过期时间（假设令牌有效期为 2 小时）
            self.expires_at =  int(expire) + time.time()

            logger.info("tenant_access_token 令牌获取成功")
            return self.tenant_access_token

        except httpx.HTTPError as e:
            # 处理 HTTP 错误
            logger.error("获取 tenant_access_token 令牌时发生 HTTP 错误", error=str(e))
            raise RuntimeError(f"获取 tenant_access_token 令牌失败: {e}")
        except Exception as e:
            # 处理其他异常
            logger.error("获取 tenant_access_token 令牌时发生意外错误", error=str(e))
            raise RuntimeError(f"意外错误: {e}")

    def _get_credentials(self):
        """
        获取认证凭据

        如果 use_headers 为 True，从 HTTP headers 获取；否则使用初始化时的值

        返回:
            tuple: (app_id, app_secret)
        """
        if self.use_headers:
            headers = get_http_headers()
            app_id = headers.get("x-lark-app-id")
            app_secret = headers.get("x-lark-app-secret")

            if not app_id or not app_secret:
                raise ValueError("需要在headers中提供 x-lark-app-id 和 x-lark-app-secret")

            return app_id, app_secret
        else:
            return self.app_id, self.app_secret

    def is_token_valid(self) -> bool:
        """
        检查当前令牌是否有效

        验证令牌是否存在且未过期。如果令牌将在 5 分钟内过期，也视为无效。

        返回:
            如果令牌存在且未过期返回 True，否则返回 False
        """
        # 检查令牌和过期时间是否存在
        if not self.tenant_access_token or not self.expires_at:
            return False

        # 检查令牌是否在 30 分钟内过期
        # 如果令牌将在 30 分钟内过期，提前刷新以避免使用过期令牌
        return time.time() < (self.expires_at - 1800)

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