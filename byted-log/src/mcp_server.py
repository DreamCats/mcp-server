"""
字节跳动 MCP 服务器实现

本模块实现了 MCP 服务器，提供 JWT 认证，支持日志查询功能。
"""

import os
import asyncio
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
import structlog

try:
    # 尝试直接导入模块（当作为包运行时）
    from auth import JWTAuthManager
    from log_query_by_id import LogQueryByID
    from log_query_by_keyword import LogQueryByKeyword
except ImportError:
    # 回退方案：当作为脚本运行时，调整导入路径
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from auth import JWTAuthManager
    from log_query_by_id import LogQueryByID
    from log_query_by_keyword import LogQueryByKeyword

# 配置结构化日志 - 使用简洁格式，避免ANSI转义字符
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
        structlog.processors.JSONRenderer()                # JSON 格式输出，避免ANSI转义字符
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 获取日志记录器实例
logger = structlog.get_logger(__name__)


class ByteDanceLogQueryMCPServer:
    """
    字节跳动 MCP 服务器

    提供服务发现工具的 MCP 服务器实现，支持 JWT 认证、PSM 服务发现、
    集群发现、实例发现和 RPC 模拟等功能。
    """

    def __init__(self):
        """
        初始化 MCP 服务器

        不再在初始化时处理 headers，而是每个客户端连接维护自己的认证上下文。
        """
        # 创建 FastMCP 实例
        self.mcp = FastMCP(
            name="byted-log-query-api", # 服务器名称
            json_response=False,        # 不使用 JSON 响应
            stateless_http=False        # 不使用无状态 HTTP
        )

        # 注册 MCP 工具
        self._register_tools()

    def _register_tools(self):
        """
        注册所有 MCP 工具

        为 MCP 服务器注册所有可用的工具函数，每个工具都提供特定的服务功能：
        - query_logs_by_logid: 日志查询

        每个工具都包含详细的中文文档字符串，描述功能、参数和返回值。
        """

        @self.mcp.tool()
        async def query_logs_by_logid(logid: str, region: str, psm_list: str = None, scan_time_min: int = 10) -> str:
            """
            根据 logid 查询日志（支持多区域智能检测）

            在多个区域（us 和 i18n）中查询指定 logid 的日志信息，支持智能区域选择。

            参数:
                logid: 要搜索的日志 ID（必需）
                psm_list: 逗号分隔的 PSM 服务列表，用于过滤（可选）
                scan_time_min: 扫描时间范围，单位为分钟（默认: 10）
                region: 目标区域 - "us", "i18n"

            返回:
                日志查询结果，包含来自最佳区域的关键信息消息

            示例:

                # 强制指定区域
                query_logs_by_logid("20250923034643559E874098ED5808B03C", region="i18n")

                # 使用 PSM 过滤
                query_logs_by_logid("20250923034643559E874098ED5808B03C", region="i18n", psm_list="oec.live.promotion_core")

            """
            try:
                # 获取当前请求的 headers
                headers = {}

                headers = get_http_headers()

                logger.info("Received headers for logid query", headers=headers)


                # 解析 PSM 列表（如果提供了）
                psm_services = None
                if psm_list:
                    psm_services = [psm.strip() for psm in psm_list.split(",") if psm.strip()]

                logger.info("Querying logs by logid", logid=logid, psm_list=psm_services,
                           scan_time_min=scan_time_min, region=region)

                # 从 headers 动态获取 cookie，默认是 cn 区域的 Cookie
                cookie_value = headers.get(f"cas_session_{region.lower()}") or headers.get("cookie") or headers.get("Cookie")
                if not cookie_value:
                    return "❌ 缺少 Cookie 认证信息，请在请求头中提供 Cookie"

                # 动态创建认证管理器
                jwt_manager = JWTAuthManager(cookie_value=cookie_value, region=region)

                # 创建临时的日志查询实例
                log_query = LogQueryByID({region: jwt_manager})

                # 使用新的多区域支持查询日志
                # result = await log_query.query_logs_by_logid(
                #     logid=logid,
                #     region=region,
                #     psm_list=psm_services,
                #     scan_time_min=scan_time_min
                # )
                result = await log_query.get_log_details(
                    logid=logid,
                    region=region,
                    psm_list=psm_services,
                    scan_time_min=scan_time_min
                )



                # 格式化响应结果
                formatted_response = log_query.format_log_response(result)

                # 清理资源
                await jwt_manager.close()

                return formatted_response

            except Exception as e:
                logger.error("Error querying logs by logid", logid=logid, error=str(e))
                return f"❌ 查询 logid {logid} 的日志时出错: {str(e)}"

        @self.mcp.tool()
        async def query_logs_by_keyword(region: str, psm_list: str, start_time: int = None,
                                      end_time: int = None, keyword_filter_include: str = None,
                                      keyword_filter_exclude: str = None, limit: int = 100) -> str:
            """
            根据关键词和时间范围查询日志（支持多区域）

            根据PSM服务列表、时间范围、关键词过滤条件，在指定区域查询符合条件的日志数据。
            支持包含关键词和排除关键词过滤。

            参数:
                region: 目标区域 - "us"（美区）、"i18n"（国际化区域）（必需）
                psm_list: 逗号分隔的PSM服务列表，用于过滤（必需，不能为空）
                start_time: 开始时间戳（秒级，可选，默认当前时间-1小时）
                end_time: 结束时间戳（秒级，可选，默认当前时间）
                keyword_filter_include: 逗号分隔的包含关键词列表（可选）
                keyword_filter_exclude: 逗号分隔的排除关键词列表（可选）
                limit: 返回结果数量限制（默认：100，最大1000）

            返回:
                日志查询结果，包含匹配的关键日志信息和统计

            示例:

                # 基本关键词查询（必须指定PSM）
                query_logs_by_keyword("us", "ttec.script.live_promotion_change")

                # 指定PSM和关键词过滤
                query_logs_by_keyword("us", "ttec.script.live_promotion_change",
                                    keyword_filter_include="error,exception")

                # 指定PSM、时间范围和关键词
                query_logs_by_keyword("us", "ttec.script.live_promotion_change",
                                    start_time=1763609508, end_time=1763616708,
                                    keyword_filter_include="stock_change")

                # 复杂关键词过滤（多个PSM）
                query_logs_by_keyword("us", "ttec.script.live_promotion_change,ttec.service.api",
                                    keyword_filter_include="stock_change,promotion",
                                    keyword_filter_exclude="debug,info")

            """
            try:
                # 获取当前请求的headers
                headers = get_http_headers()
                logger.info("Received headers for keyword query", headers=headers)

                # 验证PSM列表不能为空
                if not psm_list or not psm_list.strip():
                    return "❌ PSM服务列表不能为空，请提供至少一个PSM服务名称"

                # 解析PSM列表
                psm_services = [psm.strip() for psm in psm_list.split(",") if psm.strip()]
                if not psm_services:
                    return "❌ PSM服务列表解析失败，请检查PSM服务名称格式"

                # 解析关键词列表
                include_keywords = None
                if keyword_filter_include:
                    include_keywords = [kw.strip() for kw in keyword_filter_include.split(",") if kw.strip()]

                exclude_keywords = None
                if keyword_filter_exclude:
                    exclude_keywords = [kw.strip() for kw in keyword_filter_exclude.split(",") if kw.strip()]

                # 限制limit范围
                limit = max(1, min(limit, 1000))

                logger.info("Querying logs by keyword", region=region, psm_list=psm_services,
                           start_time=start_time, end_time=end_time,
                           include_keywords=include_keywords, exclude_keywords=exclude_keywords, limit=limit)

                # 从headers动态获取cookie
                cookie_value = headers.get(f"cas_session_{region.lower()}") or headers.get("cookie") or headers.get("Cookie")
                if not cookie_value:
                    return "❌ 缺少Cookie认证信息，请在请求头中提供Cookie"

                # 动态创建认证管理器
                jwt_manager = JWTAuthManager(cookie_value=cookie_value, region=region)

                # 创建关键词日志查询实例
                log_query = LogQueryByKeyword({region: jwt_manager})

                # 执行关键词查询
                result = await log_query.get_log_details_by_keyword(
                    region=region,
                    psm_list=psm_services,
                    start_time=start_time,
                    end_time=end_time,
                    keyword_filter_include=include_keywords,
                    keyword_filter_exclude=exclude_keywords,
                    limit=limit
                )

                # 格式化响应结果
                formatted_response = log_query.format_log_response_by_keyword(result)

                # 清理资源
                await jwt_manager.close()

                return formatted_response

            except Exception as e:
                logger.error("Error querying logs by keyword", region=region, error=str(e))
                return f"❌ 关键词查询日志时出错: {str(e)}"

    async def start(self):
        """
        启动 MCP 服务器

        不再进行认证测试，因为认证信息现在是动态获取的。
        """
        logger.info("Starting ByteDance MCP Server")

    async def stop(self):
        """
        停止 MCP 服务器并清理资源

        资源清理现在由每个请求单独处理，这里只需要简单记录日志。
        """
        logger.info("Stopping ByteDance MCP Server")

    @property
    def app(self):
        """
        获取 MCP 应用实例（用于 uvicorn）

        返回 FastMCP 应用实例，供 Web 服务器使用。
        """
        return self.mcp


def create_server() -> ByteDanceLogQueryMCPServer:
    """
    工厂函数：创建 MCP 服务器

    返回:
        ByteDanceLogQueryMCPServer 实例
    """
    return ByteDanceLogQueryMCPServer()