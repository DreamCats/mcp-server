"""
字节跳动 MCP 服务器实现

本模块实现了 MCP 服务器，提供 tenant_access_token 认证，支持 lark 相关功能。
"""

import os
import asyncio
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
import structlog

# 导入当前目录的模块
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from auth import TenantAccessTokenAuthManager
from get_note import GetNote
from get_doc import GetDoc

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


class ByteDanceLarkMCPServer:
    """
    字节跳动 MCP 服务器

    提供服务发现工具的 MCP 服务器实现，支持 tenant_access_token 认证、lark 相关功能。
    """

    def __init__(self):
        """
        初始化 MCP 服务器

        初始化认证管理器和工具类。
        """
        # 创建 FastMCP 实例
        self.mcp = FastMCP(
            name="byted-lark",    # 服务器名称
            json_response=False,        # 不使用 JSON 响应
            stateless_http=False        # 不使用无状态 HTTP
        )

        # 初始化认证管理器（从 headers 获取认证信息）
        self.auth = TenantAccessTokenAuthManager(use_headers=True)

        # 初始化工具类，传入认证管理器
        self.get_note = GetNote(self.auth)
        self.get_doc = GetDoc(self.auth)

        # 注册 MCP 工具
        self._register_tools()

    def _register_tools(self):
        """
        注册所有 MCP 工具

        为 MCP 服务器注册所有可用的工具函数，每个工具都提供特定的服务功能：
        每个工具都包含详细的中文文档字符串，描述功能、参数和返回值。
        """

        @self.mcp.tool()
        async def get_knowledge_space_node_info(
            token: str,
            obj_type: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            获取知识空间节点信息

            通过飞书API获取知识空间节点的元数据信息，包括节点类型、创建者、权限等。

            Args:
                token: 知识空间节点token，如果URL链接中token前为wiki，该token为知识库的节点token
                obj_type: 知识空间节点类型，可选值有：doc, docx, sheet, mindnote, bitable, wiki

            Returns:
                包含节点信息的字典，包括：
                - space_id: 知识空间ID
                - node_token: 知识库节点token
                - obj_token: 节点的实际云文档token
                - obj_type: 文档类型
                - parent_node_token: 父节点token
                - node_type: 节点类型（origin或shortcut）
                - origin_node_token: 快捷方式对应的实体node_token
                - origin_space_id: 快捷方式对应的实体所在的space id
                - has_child: 是否有子节点
                - title: 文档标题
                - obj_create_time: 文档创建时间
                - obj_edit_time: 文档最近编辑时间
                - node_create_time: 节点创建时间
                - creator: 文档创建者
                - owner: 文档所有者
                - node_creator: 节点创建者

            Raises:
                ValueError: 当headers中缺少必要的认证信息
                RuntimeError: 当API调用失败
            """
            logger.info(f"获取知识空间节点信息: token={token}, obj_type={obj_type}")
            try:
                result = await self.get_note.get_knowledge_space_node(token, obj_type)
                logger.info("成功获取知识空间节点信息")
                return result
            except Exception as e:
                logger.error(f"获取知识空间节点信息失败: {str(e)}")
                raise

        @self.mcp.tool()
        async def get_document_raw_content(
            document_id: str
        ) -> str:
            """
            获取文档纯文本内容

            通过飞书API获取文档的纯文本内容。

            Args:
                document_id: 文档ID，如果链接中包含docx，则链接中的token为document_id；
                          如果链接中为wiki，则需要先获取知识空间节点信息拿到obj_token作为document_id

            Returns:
                文档的纯文本内容字符串

            Raises:
                ValueError: 当headers中缺少必要的认证信息
                RuntimeError: 当API调用失败
            """
            logger.info(f"获取文档纯文本内容: document_id={document_id}")
            try:
                content = await self.get_doc.get_document_raw_content(document_id)
                logger.info("成功获取文档纯文本内容")
                return content
            except Exception as e:
                logger.error(f"获取文档纯文本内容失败: {str(e)}")
                raise


    async def start(self):
        """
        启动 MCP 服务器

        不再进行认证测试，因为认证信息现在是动态获取的。
        """
        logger.info("Starting ByteDance MCP Server")

    async def stop(self):
        """
        停止 MCP 服务器并清理资源

        关闭HTTP客户端连接。
        """
        logger.info("Stopping ByteDance MCP Server")
        # 关闭工具类的HTTP客户端
        if hasattr(self, 'get_note'):
            await self.get_note.close()
        if hasattr(self, 'get_doc'):
            await self.get_doc.close()
        # 关闭认证管理器的HTTP客户端
        if hasattr(self, 'auth'):
            await self.auth.close()

    @property
    def app(self):
        """
        获取 MCP 应用实例（用于 uvicorn）

        返回 FastMCP 应用实例，供 Web 服务器使用。
        """
        return self.mcp


def create_server() -> ByteDanceLarkMCPServer:
    """
    工厂函数：创建 MCP 服务器

    返回:
        ByteDanceLarkMCPServer 实例
    """
    return ByteDanceLarkMCPServer()