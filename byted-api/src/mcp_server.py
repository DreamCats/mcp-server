"""
字节跳动 MCP 服务器实现

本模块实现了 MCP 服务器，提供 JWT 认证和 PSM 服务发现工具。
支持多区域服务发现、集群查询、实例发现和 RPC 模拟等功能。
"""

import os
import asyncio
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import structlog

try:
    # 尝试直接导入模块（当作为包运行时）
    from auth import JWTAuthManager
    from service_discovery import PSMServiceDiscovery
    from cluster_discovery import ClusterDiscovery
    from instance_discovery import InstanceDiscovery
    from rpc_simulation import RPCSimulator
    from log_discovery import LogDiscovery
except ImportError:
    # 回退方案：当作为脚本运行时，调整导入路径
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from auth import JWTAuthManager
    from service_discovery import PSMServiceDiscovery
    from cluster_discovery import ClusterDiscovery
    from instance_discovery import InstanceDiscovery
    from rpc_simulation import RPCSimulator
    from log_discovery import LogDiscovery

# 配置结构化日志
# 设置日志处理器和格式，用于记录详细的运行信息
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,  # 按级别过滤日志
        structlog.stdlib.add_logger_name,  # 添加记录器名称
        structlog.stdlib.add_log_level,   # 添加日志级别
        structlog.stdlib.PositionalArgumentsFormatter(),  # 位置参数格式化
        structlog.processors.TimeStamper(fmt="iso"),       # ISO 时间戳
        structlog.processors.StackInfoRenderer(),          # 堆栈信息渲染
        structlog.processors.format_exc_info,              # 异常信息格式化
        structlog.processors.UnicodeDecoder(),             # Unicode 解码
        structlog.processors.JSONRenderer()                # JSON 格式输出
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 获取日志记录器实例
logger = structlog.get_logger(__name__)


class ByteDanceMCPServer:
    """
    字节跳动 MCP 服务器

    提供服务发现工具的 MCP 服务器实现，支持 JWT 认证、PSM 服务发现、
    集群发现、实例发现和 RPC 模拟等功能。
    """

    def __init__(self, headers: Dict[str, str] = None):
        """
        初始化 MCP 服务器

        根据提供的 headers 配置认证信息和区域设置，初始化各种服务发现组件。

        参数:
            headers: 可选的 headers 字典，包含 Cookie 和区域信息
                     期望的键：'cookie'、'REGION'（逗号分隔的区域列表）
        """
        # 创建 FastMCP 实例
        self.mcp = FastMCP(
            name="byted-api",           # 服务器名称
            json_response=False,        # 不使用 JSON 响应
            stateless_http=False        # 不使用无状态 HTTP
        )

        # 解析 headers 中的 Cookie 和区域配置
        self.headers = headers or {}
        self.regions = self._parse_regions_from_headers()
        self.cookies = self._parse_cookies_from_headers()

        # 初始化组件
        # 为日志发现创建区域特定的 JWT 管理器
        self.jwt_managers = {}
        for region in ["us", "i18n"]:
            cookie_value = self.cookies.get(region) or self.cookies.get("default")
            if cookie_value:
                self.jwt_managers[region] = JWTAuthManager(cookie_value=cookie_value, region=region)

        # 为其他服务创建默认的认证管理器
        default_cookie = self.cookies.get("default") or self.cookies.get("cn", "")
        self.auth_manager = JWTAuthManager(cookie_value=default_cookie, region="cn")

        # 初始化各种服务发现组件
        self.service_discovery = PSMServiceDiscovery(self.auth_manager)
        self.cluster_discovery = ClusterDiscovery(self.auth_manager)
        self.instance_discovery = InstanceDiscovery(self.auth_manager)
        self.rpc_simulator = RPCSimulator(self.auth_manager)
        self.log_discovery = LogDiscovery(self.jwt_managers)

        # 注册 MCP 工具
        self._register_tools()

    def _parse_regions_from_headers(self) -> list:
        """
        从 REGION header 解析区域列表

        解析 REGION header 中的区域配置，支持逗号分隔的多个区域。
        如果没有提供 REGION header，则返回默认区域列表。

        返回:
            区域列表，如 ["cn", "us", "i18n"]
        """
        region_header = self.headers.get("REGION", "")
        if region_header:
            # 解析逗号分隔的区域列表，转换为小写并去除空白
            return [region.strip().lower() for region in region_header.split(",") if region.strip()]
        return ["cn", "us", "i18n"]  # 默认区域列表

    def _parse_cookies_from_headers(self) -> Dict[str, str]:
        """
        从 headers 解析不同区域的 Cookie

        解析 headers 中的 Cookie 信息，支持默认 Cookie 和区域特定的 Cookie。

        返回:
            Cookie 字典，键为区域名称，值为对应的 Cookie
        """
        cookies = {}

        # 解析主要的 Cookie header（不区分大小写）
        main_cookie = self.headers.get("cookie") or self.headers.get("Cookie")
        if main_cookie:
            cookies["default"] = main_cookie

        # 解析区域特定的 Cookie
        for region in ["cn", "us", "i18n"]:
            region_cookie = self.headers.get(f"COOKIE_{region.upper()}")
            if region_cookie:
                cookies[region] = region_cookie

        return cookies

    def _register_tools(self):
        """
        注册所有 MCP 工具

        为 MCP 服务器注册所有可用的工具函数，每个工具都提供特定的服务功能：
        - search_psm_service: PSM 服务搜索
        - check_jwt_status: JWT 状态检查
        - search_multiple_services: 批量服务搜索
        - discover_clusters: 集群发现
        - discover_instances: 实例地址发现
        - simulate_rpc_request: RPC 请求模拟
        - query_logs_by_logid: 日志查询

        每个工具都包含详细的中文文档字符串，描述功能、参数和返回值。
        """

        @self.mcp.tool()
        async def search_psm_service(keyword: str) -> str:
            """
            搜索 PSM 服务信息（支持多区域并发查询）

            通过关键字搜索字节跳动的 PSM 服务，支持在海内和海外区域同时查询，
            返回最佳匹配的服务详细信息。

            参数:
                keyword: 服务关键字，用于搜索 PSM 服务（如 oec.affiliate.monitor）

            返回:
                格式化的服务信息，包含 PSM、描述、所有者、框架、部署平台等详细信息
            """
            try:
                logger.info("Searching PSM service", keyword=keyword)
                result = await self.service_discovery.get_service_details(keyword)

                # 检查是否发生错误
                if "error" in result:
                    return f"❌ 错误: {result['error']}"

                # 格式化响应结果
                service = result
                response = f"""
🔍 **服务已找到** ({result['match_type']} 匹配)

📍 **区域**: {service['region']}
🔧 **PSM**: {service['psm']}
📝 **描述**: {service['description']}
👥 **所有者**: {service['owners']}
🏗️ **框架**: {service['framework']}
🚀 **平台**: {service['deployment_platform']}
📊 **级别**: {service['level']}
🔄 **最后更新**: {service['last_updated']}
"""
                return response.strip()

            except Exception as e:
                logger.error("Error searching PSM service", keyword=keyword, error=str(e))
                return f"❌ 搜索服务时出错: {str(e)}"

        @self.mcp.tool()
        async def check_jwt_status() -> str:
            """
            检查 JWT 令牌状态和有效性

            验证当前 JWT 令牌的有效性，检查是否过期，并提供令牌的详细信息。

            返回:
                JWT 令牌状态信息，包括有效性和过期时间等详细信息
            """
            try:
                logger.info("Checking JWT status")

                # 检查令牌是否存在且有效
                if self.auth_manager.is_token_valid():
                    # 计算剩余过期时间
                    expires_in = self.auth_manager.expires_at - asyncio.get_event_loop().time()
                    minutes_left = expires_in / 60

                    return f"""
✅ **JWT 令牌状态: 有效**

⏰ **剩余时间**: {minutes_left:.1f} 分钟
🔑 **令牌存在**: 是
🔄 **自动刷新**: 已启用
""".strip()
                else:
                    # 尝试获取新令牌
                    try:
                        await self.auth_manager.get_jwt_token()
                        return """
✅ **JWT 令牌状态: 已刷新**

🔄 **新令牌获取**: 成功
⏰ **有效期**: ~60 分钟
🔑 **准备使用**: 是
""".strip()
                    except Exception as e:
                        return f"""
❌ **JWT 令牌状态: 无效**

🚨 **错误**: {str(e)}
🔧 **需要操作**: 检查 CAS_SESSION 环境变量
""".strip()

            except Exception as e:
                logger.error("Error checking JWT status", error=str(e))
                return f"❌ 检查 JWT 状态时出错: {str(e)}"

        # @self.mcp.tool()
        async def list_available_regions() -> str:
            """
            列出服务发现可用区域

            返回配置的区域列表及其状态信息。

            返回:
                配置的区域列表和状态信息
            """
            try:
                regions = self.service_discovery.regions
                response = "🌍 **可用区域**:\n\n"

                # 列出所有配置的区域
                for i, region in enumerate(regions, 1):
                    response += f"{i}. **{region}**\n"

                response += f"\n📊 **区域总数**: {len(regions)}"
                response += "\n🔄 **查询模式**: 并发查询（所有区域）"

                return response.strip()

            except Exception as e:
                logger.error("Error listing regions", error=str(e))
                return f"❌ 列出区域时出错: {str(e)}"

        @self.mcp.tool()
        async def search_multiple_services(keywords: str) -> str:
            """
            批量搜索多个 PSM 服务（逗号分隔）

            同时搜索多个 PSM 服务，支持并发查询，返回所有服务的搜索结果。

            参数:
                keywords: 逗号分隔的服务关键字列表（如 "service1,service2,service3"）

            返回:
                所有服务的搜索结果，包含每个服务的详细信息和状态
            """
            try:
                # 解析关键字列表，去除空白字符
                keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

                # 检查是否提供了有效关键字
                if not keyword_list:
                    return "❌ 请至少提供一个服务关键字"

                logger.info("Searching multiple services", keywords=keyword_list)

                # 并发搜索所有服务
                tasks = []
                for keyword in keyword_list:
                    task = self.service_discovery.get_service_details(keyword)
                    tasks.append(task)

                # 等待所有搜索任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 格式化搜索结果
                response = f"🔍 **{len(keyword_list)} 个服务的搜索结果**:\n\n"

                # 逐个处理搜索结果
                for i, (keyword, result) in enumerate(zip(keyword_list, results)):
                    if isinstance(result, Exception):
                        # 异常情况
                        response += f"{i+1}. **{keyword}** ❌ 错误: {str(result)}\n\n"
                    elif "error" in result:
                        # 搜索失败
                        response += f"{i+1}. **{keyword}** ❌ {result['error']}\n\n"
                    else:
                        # 搜索成功
                        service = result
                        response += f"{i+1}. **{keyword}** ✅ 已找到\n"
                        response += f"   📍 区域: {service['region']}\n"
                        response += f"   👥 所有者: {service['owners']}\n"
                        response += f"   🏗️ 框架: {service['framework']}\n\n"

                return response.strip()

            except Exception as e:
                logger.error("Error searching multiple services", error=str(e))
                return f"❌ 搜索服务时出错: {str(e)}"

        @self.mcp.tool()
        async def discover_clusters(psm: str) -> str:
            """
            发现指定 PSM 的集群信息（TikTok ROW 环境）

            查询指定 PSM 服务在 TikTok ROW 环境中的集群配置和部署信息。

            参数:
                psm: PSM 标识符，用于搜索集群（如 oec.affiliate.monitor）

            返回:
                指定 PSM 的集群信息，包含集群列表、区域、环境等详细信息
            """
            try:
                logger.info("Discovering clusters", psm=psm)
                result = await self.cluster_discovery.get_cluster_details(psm)

                # 格式化响应结果
                clusters = result.get('clusters', [])

                # 检查是否找到集群
                if not clusters:
                    return f"❌ 未找到 PSM: {psm} 的集群"

                # 构建响应信息
                response = f"""
📍 **集群发现结果**
🔧 **PSM**: {result['psm']}
🌍 **区域**: {result['region']}
🧪 **测试平面**: {result['test_plane']}
🖥️ **环境**: {result['environment']}

📊 **发现集群数**: {len(clusters)}
"""

                # 添加集群详细信息（限制显示前5个集群）
                for i, cluster in enumerate(clusters[:5], 1):
                    response += f"\n--- 集群 {i} ---\n"
                    for key, value in cluster.items():
                        response += f"  {key}: {value}\n"

                # 如果有更多集群，显示提示信息
                if len(clusters) > 5:
                    response += f"\n... 还有 {len(clusters) - 5} 个集群\n"

                response += f"\n⏰ **时间戳**: {result['timestamp']}"

                return response.strip()

            except Exception as e:
                logger.error("Error discovering clusters", psm=psm, error=str(e))
                return f"❌ 发现 {psm} 的集群时出错: {str(e)}"

        @self.mcp.tool()
        async def discover_instances(psm: str, zone: str, idc: str, cluster: str = None) -> str:
            """
            发现指定 PSM 的实例地址（需要区域和 IDC 过滤器）

            查询指定 PSM 服务在特定区域和 IDC 中的实例地址信息。

            参数:
                psm: PSM 标识符，用于搜索实例（如 oec.affiliate.monitor）
                zone: 区域过滤器（必需，如 "MVAALI", "SGALI"）
                idc: IDC 过滤器（必需，如 "maliva", "my", "sg1"）
                cluster: 集群过滤器（可选，如未提供则默认为 "default"）

            返回:
                指定 PSM 的实例地址信息，包含实例列表、过滤器信息等

            注意:
                zone 和 idc 是基于 API 要求的必需参数。如果未指定 cluster，
                它将默认为 "default"。
            """
            try:
                logger.info("Discovering instances", psm=psm, zone=zone, idc=idc, cluster=cluster)
                result = await self.instance_discovery.get_instance_details(psm, zone, idc, cluster)

                # 格式化响应结果
                instances = result.get('instances', [])

                # 检查是否找到实例
                if not instances:
                    return f"❌ 未找到 PSM: {psm} 的实例"

                # 构建基础响应信息
                response = f"""
📍 **实例发现结果**
🔧 **PSM**: {result['psm']}
🖥️ **环境**: {result['environment']}

📊 **发现实例数**: {len(instances)}
"""

                # 添加过滤器信息（如果提供了有效过滤器）
                filters = result.get('filters', {})
                active_filters = {k: v for k, v in filters.items() if v is not None}
                if active_filters:
                    response += "\n🔍 **有效过滤器**:\n"
                    for key, value in active_filters.items():
                        response += f"  {key}: {value}\n"

                # 添加实例详细信息（限制显示前5个实例）
                for i, instance in enumerate(instances[:5], 1):
                    response += f"\n--- 实例 {i} ---\n"
                    if isinstance(instance, dict):
                        # 字典格式：显示所有键值对
                        for key, value in instance.items():
                            response += f"  {key}: {value}\n"
                    elif isinstance(instance, str):
                        # 字符串格式：显示地址信息
                        response += f"  地址: {instance}\n"
                    else:
                        # 其他格式：直接显示
                        response += f"  实例: {instance}\n"

                # 如果有更多实例，显示提示信息
                if len(instances) > 5:
                    response += f"\n... 还有 {len(instances) - 5} 个实例\n"

                response += f"\n⏰ **时间戳**: {result['timestamp']}"

                return response.strip()

            except Exception as e:
                logger.error("Error discovering instances", psm=psm, error=str(e))
                return f"❌ 发现 {psm} 的实例时出错: {str(e)}"

        @self.mcp.tool()
        async def simulate_rpc_request(psm: str, address: str, func_name: str, req_body: str,
                                     zone: str, idc: str, cluster: str = "default",
                                     env: str = "prod", request_timeout: int = 60000) -> str:
            """
            向 i18n 服务发送 RPC 请求模拟（使用已发现的实例地址）

            通过指定的实例地址发送 RPC 调用请求，模拟真实的 RPC 调用过程。

            参数:
                psm: PSM 标识符（必需，如 "oec.affiliate.monitor"）
                address: 目标实例地址，格式为 [ip]:port（必需）
                func_name: RPC 方法名称（必需，如 "SearchLiveEvent"）
                req_body: JSON 字符串格式的请求体（必需）
                zone: 地理区域标识符（必需，如 "MVAALI", "SGALI"）
                idc: 数据中心标识符（必需，如 "maliva", "my", "sg1"）
                cluster: 集群名称（可选，默认为 "default"）
                env: 环境类型（可选，默认为 "prod"）
                request_timeout: 请求超时时间，单位为毫秒（可选，默认为 60000）

            返回:
                RPC 响应，包含响应体、性能指标和调试信息等详细内容

            示例:
                simulate_rpc_request(
                    psm="oec.affiliate.monitor",
                    address="[fdbd:dc61:2:151::195]:11503",
                    func_name="SearchLiveEvent",
                    req_body='{"room_id": "1730849136927543871", "author_id": "7280819145410593838"}',
                    zone="MVAALI",
                    idc="maliva"
                )
            """
            try:
                logger.info("Simulating RPC request",
                           psm=psm, address=address, func_name=func_name,
                           zone=zone, idc=idc, cluster=cluster, env=env)

                # 执行 RPC 请求模拟
                result = await self.rpc_simulator.simulate_rpc_request(
                    psm=psm,
                    address=address,
                    func_name=func_name,
                    req_body=req_body,
                    zone=zone,
                    idc=idc,
                    cluster=cluster,
                    env=env,
                    request_timeout=request_timeout
                )

                # 使用模拟器的格式化器格式化响应
                formatted_response = self.rpc_simulator.format_rpc_response(result)
                return formatted_response

            except Exception as e:
                logger.error("Error simulating RPC request", error=str(e))
                return f"❌ RPC 请求模拟时出错: {str(e)}"

        @self.mcp.tool()
        async def query_logs_by_logid(logid: str, psm_list: str = None, scan_time_min: int = 10,
                                    region: str = "all") -> str:
            """
            根据 logid 查询日志（支持多区域智能检测）

            在多个区域（us 和 i18n）中查询指定 logid 的日志信息，支持智能区域选择。

            参数:
                logid: 要搜索的日志 ID（必需）
                psm_list: 逗号分隔的 PSM 服务列表，用于过滤（可选）
                scan_time_min: 扫描时间范围，单位为分钟（默认: 10）
                region: 目标区域 - "all", "us", "i18n"（默认: "all"）

            返回:
                日志查询结果，包含来自最佳区域的关键信息消息

            示例:

                # 强制指定区域
                query_logs_by_logid("20250923034643559E874098ED5808B03C", region="i18n")

                # 使用 PSM 过滤
                query_logs_by_logid("20250923034643559E874098ED5808B03C", psm_list="oec.live.promotion_core")

                # 并发查询所有区域
                query_logs_by_logid("20250923034643559E874098ED5808B03C", region="all")
            """
            try:
                # 解析 PSM 列表（如果提供了）
                psm_services = None
                if psm_list:
                    psm_services = [psm.strip() for psm in psm_list.split(",") if psm.strip()]

                logger.info("Querying logs by logid", logid=logid, psm_list=psm_services,
                           scan_time_min=scan_time_min, region=region)

                # 使用新的多区域支持查询日志
                result = await self.log_discovery.get_log_details(
                    logid=logid,
                    psm_list=psm_services,
                    scan_time_min=scan_time_min,
                    region=region
                )

                # 格式化响应结果
                formatted_response = self.log_discovery.format_log_response(result)
                return formatted_response

            except Exception as e:
                logger.error("Error querying logs by logid", logid=logid, error=str(e))
                return f"❌ 查询 logid {logid} 的日志时出错: {str(e)}"

    async def start(self):
        """
        启动 MCP 服务器

        初始化服务器并测试认证连接，确保服务可以正常运行。
        """
        logger.info("Starting ByteDance MCP Server")

        # 启动时测试认证
        try:
            await self.auth_manager.get_jwt_token()
            logger.info("JWT authentication test successful")
        except Exception as e:
            logger.warning("JWT authentication test failed", error=str(e))
            logger.warning("Server will still start but authentication may fail")

    async def stop(self):
        """
        停止 MCP 服务器并清理资源

        优雅地关闭所有组件，释放资源，确保没有内存泄漏。
        """
        logger.info("Stopping ByteDance MCP Server")

        # 清理资源
        try:
            # 关闭主认证管理器
            await self.auth_manager.close()

            # 关闭区域特定的 JWT 管理器
            for jwt_manager in self.jwt_managers.values():
                await jwt_manager.close()

            # 关闭所有服务发现组件
            await self.service_discovery.close()
            await self.cluster_discovery.close()
            await self.instance_discovery.close()
            await self.rpc_simulator.close()
            await self.log_discovery.close()

            logger.info("Resources cleaned up successfully")
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))

    @property
    def app(self):
        """
        获取 MCP 应用实例（用于 uvicorn）

        返回 FastMCP 应用实例，供 Web 服务器使用。
        """
        return self.mcp


def create_server(headers: Dict[str, str] = None) -> ByteDanceMCPServer:
    """
    工厂函数：创建 MCP 服务器

    参数:
        headers: 可选的 headers 字典，包含 Cookie 和区域信息

    返回:
        ByteDanceMCPServer 实例
    """
    return ByteDanceMCPServer(headers=headers)