"""
字节跳动 MCP 服务器 PSM 服务发现模块

本模块处理多区域并发 PSM 服务查询，支持在海内和海外区域同时搜索服务信息。
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

# 获取日志记录器实例
logger = structlog.get_logger(__name__)


class PSMServiceDiscovery:
    """
    PSM 服务发现器

    提供多区域并发查询功能，支持在海内和海外 Neptune 服务注册中心同时搜索 PSM 服务。
    """

    def __init__(self, jwt_manager):
        """
        初始化 PSM 服务发现器

        参数:
            jwt_manager: JWTAuthManager 实例，用于认证
        """
        self.jwt_manager = jwt_manager  # JWT 认证管理器

        # 配置多区域服务发现端点
        # 包含海内和海外两个区域的 Neptune 服务注册中心
        self.regions = [
            "https://ms-neptune.byted.org",      # 海内区域
            "https://ms-neptune.tiktok-us.org"  # 海外区域
        ]

        # 配置 HTTP 客户端
        # 设置合适的超时时间和请求头，模拟浏览器行为
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30秒超时
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    async def search_service(self, keyword: str) -> Dict[str, Any]:
        """
        搜索 PSM 服务（支持多区域并发查询）

        在多个区域中并发搜索指定的 PSM 服务，返回最佳匹配结果。

        参数:
            keyword: 服务关键字，用于搜索 PSM 服务

        返回:
            来自最佳匹配区域的服务信息

        Raises:
            RuntimeError: If all regions fail
        """
        logger.info("Searching PSM service", keyword=keyword)

        # Get JWT token
        jwt_token = await self.jwt_manager.get_jwt_token()

        # Create concurrent tasks for all regions
        tasks = []
        for region in self.regions:
            task = self._search_single_region(region, keyword, jwt_token)
            tasks.append(task)

        # Execute concurrent requests
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Select best result
        best_result = self._select_best_result(results, keyword)

        if best_result:
            logger.info("Service found", region=best_result.get("region"), psm=keyword)
            return best_result
        else:
            logger.warning("No matching service found", keyword=keyword)
            return {"error": f"No matching service found for keyword: {keyword}"}

    async def _search_single_region(self, region: str, keyword: str, jwt_token: str) -> Dict[str, Any]:
        """
        在单个区域中搜索 PSM 服务

        向指定的区域发送 HTTP 请求，搜索匹配的 PSM 服务信息。

        参数:
            region: 区域基础 URL（如 https://ms-neptune.byted.org）
            keyword: 搜索关键字，用于匹配 PSM 服务
            jwt_token: JWT 认证令牌，用于 API 访问认证

        返回:
            包含区域信息的搜索结果字典，格式为：
            {
                "region": 区域URL,
                "data": 服务数据列表,
                "timestamp": 时间戳,
                "error": 错误信息（如果有）
            }
        """
        url = f"{region}/api/neptune/ms/service/search"
        headers = {"x-jwt-token": jwt_token}
        params = {
            "keyword": keyword,
            "search_type": "all"
        }

        try:
            logger.debug("Searching region", region=region, keyword=keyword)

            # 发送 HTTP GET 请求到 Neptune 服务搜索 API
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()  # 检查 HTTP 状态码，如果不是 2xx 会抛出异常

            # 解析 JSON 响应数据
            data = response.json()

            # 检查服务是否找到（error_code 为 0 表示成功，且 data 字段有内容）
            if data.get("error_code") == 0 and data.get("data"):
                # 构建成功的结果字典，添加区域信息和时间戳
                result = {
                    "region": region,
                    "data": data["data"],
                    "timestamp": datetime.now().isoformat()
                }
                logger.debug("Service found in region", region=region, count=len(data["data"]))
                return result
            else:
                # 服务未找到的情况
                logger.debug("No service found in region", region=region, error_code=data.get("error_code"))
                return {"region": region, "data": [], "error": "No matching service"}

        except httpx.TimeoutException:
            # 请求超时异常处理
            logger.warning("Region search timeout", region=region, keyword=keyword)
            return {"region": region, "error": "Timeout"}

        except httpx.HTTPError as e:
            # HTTP 错误异常处理
            logger.error("Region search HTTP error", region=region, keyword=keyword, error=str(e))
            return {"region": region, "error": f"HTTP error: {e}"}

        except Exception as e:
            # 其他未预期的异常处理
            logger.error("Region search unexpected error", region=region, keyword=keyword, error=str(e))
            return {"region": region, "error": f"Unexpected error: {e}"}

    def _select_best_result(self, results: List[Any], keyword: str) -> Optional[Dict[str, Any]]:
        """
        从多个区域的结果中选择最佳匹配结果

        根据搜索结果的质量和相关性，选择最佳的 PSM 服务匹配结果。
        优先选择 PSM 完全匹配的服务，如果没有完全匹配则返回第一个有效结果。

        参数:
            results: 来自所有区域的搜索结果列表
            keyword: 原始的搜索关键字（期望的 PSM 名称）

        返回:
            最佳匹配结果字典，包含以下字段：
            - region: 结果来源区域
            - service: 匹配的服务信息
            - match_type: 匹配类型（"exact" 精确匹配 或 "fallback" 回退匹配）
            如果没有有效结果则返回 None
        """
        valid_results = []

        # 遍历所有区域的结果，筛选有效结果
        for result in results:
            # 跳过异常结果
            if isinstance(result, Exception):
                logger.warning("Region search threw exception", error=str(result))
                continue

            # 跳过包含错误的结果
            if result.get("error"):
                logger.debug("Region returned error", region=result.get("region"), error=result["error"])
                continue

            # 检查是否有匹配的服务数据
            if result.get("data") and len(result["data"]) > 0:
                # 首先查找完全匹配的 PSM（精确匹配优先级最高）
                for service in result["data"]:
                    if service.get("psm") == keyword:
                        logger.info("Found exact PSM match", region=result["region"], psm=keyword)
                        return {
                            "region": result["region"],
                            "service": service,
                            "match_type": "exact"  # 标记为精确匹配
                        }

                # 没有找到精确匹配，存储有效结果用于后续回退
                valid_results.append(result)

        # 如果没有精确匹配，使用第一个有效结果作为回退
        if valid_results:
            best = valid_results[0]
            logger.info("Using first valid result as fallback", region=best["region"], count=len(best["data"]))
            return {
                "region": best["region"],
                "service": best["data"][0],  # 使用第一个服务作为回退
                "match_type": "fallback"  # 标记为回退匹配
            }

        return None  # 没有找到任何有效结果

    async def get_service_details(self, psm: str) -> Dict[str, Any]:
        """
        获取指定 PSM 的详细信息

        通过搜索服务获取指定 PSM 的完整详细信息，包括描述、所有者、框架等。

        参数:
            psm: PSM 标识符，格式如 "oec.affiliate.monitor"

        返回:
            详细的服务信息字典，包含以下字段：
            - psm: PSM 名称
            - description: 服务描述
            - owners: 服务所有者
            - framework: 使用的框架
            - deployment_platform: 部署平台
            - level: 服务级别
            - region: 服务所在区域
            - match_type: 匹配类型（精确/回退）
            - last_updated: 最后更新时间

            如果发生错误，返回包含 error 字段的字典
        """
        result = await self.search_service(psm)

        # 如果搜索过程中发生错误，直接返回错误结果
        if "error" in result:
            return result

        # 格式化详细响应，提取关键服务信息
        service = result["service"]
        return {
            "psm": service.get("psm"),                                    # PSM 名称
            "description": service.get("description", "No description available"),  # 服务描述
            "owners": service.get("owners", "Unknown"),                   # 服务所有者
            "framework": service.get("framework", "Unknown"),             # 使用的技术框架
            "deployment_platform": service.get("deployment_platform", "Unknown"),  # 部署平台
            "level": service.get("level", "Unknown"),                     # 服务级别
            "region": result["region"],                                   # 服务所在区域
            "match_type": result["match_type"],                           # 匹配类型（精确/回退）
            "last_updated": service.get("updated_at", "Unknown")          # 最后更新时间
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