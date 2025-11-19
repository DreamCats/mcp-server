"""
字节跳动 MCP 服务器实例地址发现模块

本模块处理 TikTok ROW 环境中的实例地址发现查询，提供基于 JWT 认证的
服务实例地址检索功能。支持通过 PSM、区域、IDC 等参数查询服务实例地址。
"""

from typing import Dict, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class InstanceDiscovery:
    """
    TikTok ROW 实例地址发现器

    提供基于 JWT 认证的实例地址查询功能，支持通过 PSM 标识符、
    区域（zone）、IDC 等参数查询服务实例的地址信息。
    """

    def __init__(self, jwt_manager):
        """
        初始化实例地址发现器

        参数:
            jwt_manager: JWTAuthManager 实例，用于处理 JWT 认证
        """

    def __init__(self, jwt_manager):
        """
        初始化实例地址发现器

        参数:
            jwt_manager: JWTAuthManager 实例，用于处理 JWT 认证
        """
        self.jwt_manager = jwt_manager  # JWT 认证管理器

        # TikTok ROW 实例地址发现 API 端点
        self.discovery_url = "https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/addrs"

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

    async def discover_instances(self, psm: str, zone: str, idc: str,
                               cluster: Optional[str] = None) -> Dict[str, Any]:
        """
        发现指定 PSM 的实例地址（需要区域和 IDC 过滤器）

        通过 TikTok ROW API 查询指定 PSM 服务在特定区域和 IDC 中的实例地址信息。

        参数:
            psm: PSM 标识符，用于搜索实例（必需，如 "oec.affiliate.monitor"）
            zone: 区域过滤器（必需，如 "MVAALI", "SGALI"）
            idc: IDC 过滤器（必需，如 "maliva", "my", "sg1"）
            cluster: 集群过滤器（可选，如未提供则默认为 "default"）

        返回:
            实例地址信息字典，包含以下字段：
            - psm: PSM 名称
            - filters: 使用的过滤器（zone, idc, cluster）
            - data: 原始 API 响应数据
            - timestamp: 查询时间戳

        异常:
            RuntimeError: 当实例发现失败时抛出，包含具体的错误信息

        注意:
            zone 和 idc 是基于 API 要求的必需参数。如果未指定 cluster，
            它将默认为 "default"。
        """
        logger.info("Discovering instances", psm=psm, zone=zone, idc=idc, cluster=cluster)

        # 获取 JWT 认证令牌
        jwt_token = await self.jwt_manager.get_jwt_token()

        # 准备 API 请求参数
        headers = {"x-jwt-token": jwt_token}  # JWT 认证头
        params = {
            "psm": psm,           # PSM 标识符
            "env": "prod",        # 生产环境
            "zone": zone,         # 区域过滤器
            "idc": idc            # IDC 过滤器
        }

        # 添加集群参数，如未提供则默认为 "default"
        params["cluster"] = cluster if cluster is not None else "default"

        try:
            logger.debug("Querying instance discovery API", url=self.discovery_url, psm=psm, headers=headers, params=params)

            # 发送 HTTP GET 请求到实例地址发现 API
            response = await self.client.get(self.discovery_url, headers=headers, params=params)
            response.raise_for_status()  # 检查 HTTP 状态码

            # 解析 JSON 响应数据
            data = response.json()

            # 记录响应详情用于调试（已注释掉，避免日志过于冗长）
            # logger.debug("Instance discovery response",
            #             status_code=response.status_code,
            #             response_headers=dict(response.headers),
            #             response_data=data)

            # 格式化响应结果
            result = {
                "psm": psm,                                    # PSM 名称
                "filters": {                                   # 使用的过滤器
                    "zone": zone,
                    "idc": idc,
                    "cluster": cluster
                },
                "data": data,                                  # 原始 API 响应数据
                "timestamp": datetime.now().isoformat()      # 查询时间戳
            }

            # 计算发现的实例数量
            instances_count = len(data.get("data", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("Instance discovery completed", psm=psm, instances_found=instances_count, status_code=response.status_code)
            return result

        except httpx.TimeoutException:
            # 请求超时异常处理
            logger.warning("Instance discovery timeout", psm=psm)
            raise RuntimeError(f"Timeout while discovering instances for PSM: {psm}")

        except httpx.HTTPError as e:
            # HTTP 错误异常处理
            logger.error("Instance discovery HTTP error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while discovering instances for PSM {psm}: {e}")

        except Exception as e:
            # 其他未预期的异常处理
            logger.error("Instance discovery unexpected error", psm=psm, error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while discovering instances for PSM {psm}: {e}")

    async def get_instance_details(self, psm: str, zone: str, idc: str,
                                 cluster: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定 PSM 的详细实例地址信息

        处理实例地址发现 API 的响应数据，提取并格式化实例地址详细信息。

        参数:
            psm: PSM 标识符（必需）
            zone: 区域过滤器（必需，如 "MVAALI", "SGALI"）
            idc: IDC 过滤器（必需，如 "maliva", "my", "sg1"）
            cluster: 集群过滤器（可选，如未提供则默认为 "default"）

        返回:
            详细的实例地址信息字典，包含以下字段：
            - psm: PSM 名称
            - instances: 实例列表（包含每个实例的地址信息）
            - environment: 环境类型（如 prod）
            - filters: 使用的过滤器信息
            - timestamp: 查询时间戳

        注意:
            zone 和 idc 是基于 API 要求的必需参数。如果未指定 cluster，
            它将默认为 "default"。
        """
        result = await self.discover_instances(psm, zone, idc, cluster)

        # 格式化详细响应，处理不同的 API 响应结构
        data = result.get("data", {})

        # 调试日志：记录数据结构信息用于分析
        logger.debug("Formatting instance details", data_type=type(data), data_content=data)

        # 处理实际的 API 响应结构，支持多种可能的数据格式
        if isinstance(data, dict) and "data" in data:
            # 标准格式：响应包含 data 字段
            instances = data.get("data", [])
        elif isinstance(data, list):
            # 简化格式：直接返回列表
            instances = data
        else:
            # 未知格式：返回空列表
            instances = []

        logger.debug("Extracted instances", instances_count=len(instances))

        # 构建最终的详细实例地址信息响应
        return {
            "psm": psm,                                    # PSM 名称
            "instances": instances,                          # 实例列表
            "environment": "prod",                           # 环境类型
            "filters": result.get("filters", {}),         # 使用的过滤器信息
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