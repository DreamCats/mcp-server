"""
字节跳动 MCP 服务器实现

本模块实现了 MCP 服务器，提供 JWT 认证，支持Bits相关查询功能。
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
    from bits_query_task_changes import BitsQueryForTaskChanges
except ImportError:
    # 回退方案：当作为脚本运行时，调整导入路径
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from auth import JWTAuthManager
    from bits_query_task_changes import BitsQueryForTaskChanges

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


class ByteDanceBitsQueryMCPServer:
    """
    字节跳动 MCP 服务器

    提供服务发现工具的 MCP 服务器实现，支持 JWT 认证、Bits相关查询功能。
    """

    def __init__(self):
        """
        初始化 MCP 服务器

        不再在初始化时处理 headers，而是每个客户端连接维护自己的认证上下文。
        """
        # 创建 FastMCP 实例
        self.mcp = FastMCP(
            name="byted-bits-query",    # 服务器名称
            json_response=False,        # 不使用 JSON 响应
            stateless_http=False        # 不使用无状态 HTTP
        )

        # 注册 MCP 工具
        self._register_tools()

    def _register_tools(self):
        """
        注册所有 MCP 工具

        为 MCP 服务器注册所有可用的工具函数，每个工具都提供特定的服务功能：
            - query_bits_task_changes: 查询 Bits 平台开发任务变更信息
            -
        每个工具都包含详细的中文文档字符串，描述功能、参数和返回值。
        """

        @self.mcp.tool()
        async def query_bits_task_changes(dev_basic_id: int) -> str:
            """
            查询 Bits 平台开发任务变更信息

            根据开发任务基础 ID (devBasicId) 查询相关的开发任务、代码变更、评审状态等信息。
            支持查询代码合并请求 (MR)、分支信息、代码统计、评审状态等详细数据。

            参数:
                dev_basic_id: 开发任务基础 ID，必须是正整数

            返回:
                格式化的任务查询结果，包含：
                - 任务基本信息（ID、创建者、标题、状态）
                - 代码变更详情（仓库、分支、MR 信息）
                - 代码统计（新增/删除行数）
                - 评审信息（评审者、状态、通过/拒绝数）
                - 提交信息（最新提交 ID、标题）

            异常:
                当 dev_basic_id 无效或查询失败时返回错误信息

            示例:
                query_bits_task_changes(1862036)
            """
            try:
                # 获取请求头中的认证信息
                headers = get_http_headers()

                # 从请求头中提取 JWT 令牌
                cookie_value = headers.get("CAS_SESSION", "") or headers.get("cas_session", "")
                if not cookie_value:
                    return "❌ 错误：缺少 CAS_SESSION 认证令牌。请在请求头中提供有效的 CAS_SESSION 头。"

                # 创建 JWT 认证管理器
                jwt_manager = JWTAuthManager(cookie_value)

                # 创建 Bits 查询器
                bits_query = BitsQueryForTaskChanges(jwt_manager)

                try:
                    # 获取任务详细信息
                    task_details = await bits_query.get_task_details(dev_basic_id)

                    # 格式化响应
                    formatted_response = bits_query.format_task_response(task_details)

                    return formatted_response

                finally:
                    # 清理资源
                    await bits_query.close()
                    await jwt_manager.close()

            except ValueError as e:
                return f"❌ 参数错误：{str(e)}"
            except RuntimeError as e:
                return f"❌ 查询失败：{str(e)}"
            except Exception as e:
                logger.error("查询 Bits 任务时发生未预期错误", error=str(e), error_type=type(e).__name__)
                return f"❌ 查询失败：发生未预期的错误 - {str(e)}"





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


def create_server() -> ByteDanceBitsQueryMCPServer:
    """
    工厂函数：创建 MCP 服务器

    返回:
        ByteDanceBitsQueryMCPServer 实例
    """
    return ByteDanceBitsQueryMCPServer()