"""
字节跳动 MCP 服务器集群发现模块

本模块处理 TikTok ROW 环境中的集群发现查询，提供基于 JWT 认证的集群信息检索功能。
支持通过 PSM 标识符查询服务集群配置和部署信息。
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class ClusterDiscovery:
    """
    TikTok ROW 集群发现器

    提供基于 JWT 认证的集群信息查询功能，支持通过 PSM 标识符
    发现服务在 TikTok ROW 环境中的集群配置和部署详情。
    """

    def __init__(self, jwt_manager):
        """
        初始化集群发现器

        参数:
            jwt_manager: JWTAuthManager 实例，用于处理 JWT 认证
        """

    def __init__(self, jwt_manager):
        """
        初始化集群发现器

        参数:
            jwt_manager: JWTAuthManager 实例，用于处理 JWT 认证
        """
        self.jwt_manager = jwt_manager  # JWT 认证管理器

        # TikTok ROW 集群发现 API 端点
        self.discovery_url = "https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/plane/clusters"

        # 配置 HTTP 客户端
        # 设置合适的超时时间和请求头，模拟浏览器行为以提高兼容性
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30秒超时
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    async def discover_clusters(self, psm: str) -> Dict[str, Any]:
        """
        发现指定 PSM 的集群信息

        通过 TikTok ROW API 查询指定 PSM 服务的集群配置和部署信息。

        参数:
            psm: PSM 标识符，用于搜索集群信息（如 "oec.affiliate.monitor"）

        返回:
            集群信息字典，包含以下字段：
            - psm: PSM 名称
            - data: 原始 API 响应数据
            - timestamp: 查询时间戳

        异常:
            RuntimeError: 当集群发现失败时抛出，包含具体的错误信息
        """
        logger.info("Discovering clusters", psm=psm)

        # 获取 JWT 认证令牌
        jwt_token = await self.jwt_manager.get_jwt_token()

        # 准备 API 请求参数
        headers = {"x-jwt-token": jwt_token}  # JWT 认证头
        params = {
            "psm": psm,           # PSM 标识符
            "test_plane": "1",    # 测试平面标识
            "env": "prod"         # 生产环境标识
        }

        try:
            logger.debug("Querying cluster discovery API", url=self.discovery_url, psm=psm, headers=headers, params=params)

            # 发送 HTTP GET 请求到集群发现 API
            response = await self.client.get(self.discovery_url, headers=headers, params=params)
            response.raise_for_status()  # 检查 HTTP 状态码

            # 解析 JSON 响应数据
            data = response.json()

            # 记录响应详情用于调试（已注释掉，避免日志过于冗长）
            # logger.debug("Cluster discovery response",
            #             status_code=response.status_code,
            #             response_headers=dict(response.headers),
            #             response_data=data)

            # 格式化响应结果
            result = {
                "psm": psm,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            # 计算发现的集群数量
            clusters_count = len(data.get("data", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("Cluster discovery completed", psm=psm, clusters_found=clusters_count, status_code=response.status_code)
            return result

        except httpx.TimeoutException:
            # 请求超时异常处理
            logger.warning("Cluster discovery timeout", psm=psm)
            raise RuntimeError(f"Timeout while discovering clusters for PSM: {psm}")

        except httpx.HTTPError as e:
            # HTTP 错误异常处理
            logger.error("Cluster discovery HTTP error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while discovering clusters for PSM {psm}: {e}")

        except Exception as e:
            # 其他未预期的异常处理
            logger.error("Cluster discovery unexpected error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while discovering clusters for PSM {psm}: {e}")

    async def get_cluster_details(self, psm: str) -> Dict[str, Any]:
        """
        获取指定 PSM 的详细集群信息

        处理集群发现 API 的响应数据，提取并格式化集群详细信息，
        包括集群列表、区域信息、环境配置等。

        参数:
            psm: PSM 标识符，用于查询集群信息

        返回:
            详细的集群信息字典，包含以下字段：
            - psm: PSM 名称
            - clusters: 集群列表（包含每个集群的详细信息）
            - region: 集群所在区域
            - environment: 环境类型（如 prod）
            - test_plane: 测试平面标识
            - timestamp: 查询时间戳
        """
        result = await self.discover_clusters(psm)

        # 格式化详细响应，处理不同的 API 响应结构
        data = result.get("data", {})

        # 调试日志：记录数据结构信息用于分析
        logger.debug("Formatting cluster details", data_type=type(data), data_content=data)

        # 处理实际的 API 响应结构，支持多种可能的数据格式
        if isinstance(data, dict) and "data" in data:
            # 标准格式：响应包含 data 字段
            clusters = data.get("data", [])
            # 尝试从集群数据中提取区域信息
            if clusters and len(clusters) > 0:
                # 从第一个集群的区域显示名称获取区域信息
                first_cluster = clusters[0]
                region = first_cluster.get("zone_display_name", "Unknown")
            else:
                region = "Unknown"
        elif isinstance(data, list):
            # 简化格式：直接返回列表
            clusters = data
            # 从第一个集群的区域显示名称获取区域信息
            if clusters and len(clusters) > 0:
                first_cluster = clusters[0]
                region = first_cluster.get("zone_display_name", "Unknown")
            else:
                region = "Unknown"
        else:
            # 未知格式：返回空列表
            clusters = []
            region = "Unknown"

        logger.debug("Extracted clusters", clusters_count=len(clusters), region=region)

        # 构建最终的详细集群信息响应
        return {
            "psm": psm,                                    # PSM 名称
            "clusters": clusters,                          # 集群列表
            "region": region,                              # 区域信息
            "environment": "prod",                         # 环境类型
            "test_plane": "1",                            # 测试平面标识
            "timestamp": result.get("timestamp", "Unknown")  # 查询时间戳
        }

    async def close(self):
        """关闭 HTTP 客户端连接"""
        await self.client.aclose()

    def __del__(self):
        """对象销毁时的清理工作

        确保在对象被垃圾回收时关闭 HTTP 客户端连接，避免资源泄漏。
        使用异步方式安全地关闭客户端，处理可能的循环引用问题。
        """
        try:
            if hasattr(self, 'client'):
                import asyncio
                # 检查事件循环是否正在运行，避免在事件循环未运行时创建任务
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.client.aclose())
        except Exception:
            # 忽略清理过程中的任何异常，避免影响正常的垃圾回收
            pass