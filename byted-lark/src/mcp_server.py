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
from create_doc import CreateDoc
from convert_block import ConvertBlock
from create_block import CreateBlock
from upload_all import UploadAll
from update_blocks import UpdateBlocks
from add_permission_member import AddPermissionMember

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
        self.create_doc = CreateDoc(self.auth)
        self.convert_block = ConvertBlock(self.auth)
        self.create_block = CreateBlock(self.auth)
        self.upload_all = UploadAll(self.auth)
        self.update_blocks = UpdateBlocks(self.auth)
        self.add_permission_member = AddPermissionMember(self.auth)

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

        @self.mcp.tool()
        async def create_document(
            folder_token: Optional[str] = None,
            title: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            创建新文档

            通过飞书API创建新的docx文档。

            Args:
                folder_token: 可选，指定文档所在文件夹的Token
                title: 可选，文档标题，只支持纯文本，长度范围1～800字符

            Returns:
                包含文档信息的字典：
                - document_id: 创建的文档ID
                - revision_id: 文档版本ID
                - title: 文档标题

            Raises:
                ValueError: 当headers中缺少必要的认证信息
                RuntimeError: 当API调用失败
            """
            logger.info(f"创建文档: folder_token={folder_token}, title={title}")
            try:
                result = await self.create_doc.create_document(folder_token, title)
                logger.info("成功创建文档")
                result["url"] = f"https://bytedance.larkoffice.com/docx/{result['document_id']}"
                return result
            except Exception as e:
                logger.error(f"创建文档失败: {str(e)}")
                raise

        @self.mcp.tool()
        async def convert_content_to_blocks(
            content: str,
            content_type: str = "markdown"
        ) -> Dict[str, Any]:
            """
            将Markdown/HTML内容转换为文档块

            通过飞书API将Markdown或HTML格式的内容转换为文档块。

            Args:
                content: Markdown或HTML格式的内容
                content_type: 内容类型，支持"markdown"或"html"

            Returns:
                包含转换结果的字典：
                - first_level_block_ids: 一级块ID列表，创建块的 children_id
                - blocks: 转换后的块对象列表
                - block_id_to_image_urls: 块ID到图片URL的映射

            Raises:
                ValueError: 当headers中缺少必要的认证信息或content_type无效
                RuntimeError: 当API调用失败
            """
            logger.info(f"转换内容为文档块: content_type={content_type}")
            try:
                result = await self.convert_block.convert_content_to_blocks(content, content_type)
                logger.info("成功转换内容为文档块")
                return result
            except Exception as e:
                logger.error(f"转换内容为文档块失败: {str(e)}")
                raise

        @self.mcp.tool()
        async def create_nested_blocks(
            document_id: str,
            block_id: str,
            children_id: list,
            descendants: list,
            index: int = 0,
            document_revision_id: int = -1,
            client_token: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            在文档中创建嵌套块

            通过飞书API在文档中创建嵌套块结构。

            Args:
                document_id: 文档ID
                block_id: 父块ID（根级别使用空字符串）
                children_id: 要插入的子块ID列表，比如，通过convert_content_to_blocks 获取 first_level_block_ids
                descendants: 后代块对象列表及其属性
                index: 插入位置索引（默认0）
                document_revision_id: 文档版本ID（默认-1表示最新版本）
                client_token: 可选的UUIDv4，用于幂等更新

            Returns:
                包含创建结果的字典：
                - block_id_relations: 临时块ID到实际块ID的映射
                - children: 创建的子块列表
                - client_token: 操作标识符
                - document_revision_id: 新的文档版本ID

            Raises:
                ValueError: 当headers中缺少必要的认证信息
                RuntimeError: 当API调用失败
            """
            logger.info(f"创建嵌套块: document_id={document_id}, block_id={block_id}")
            try:
                result = await self.create_block.create_nested_blocks(
                    document_id, block_id, children_id, descendants,
                    index, document_revision_id, client_token
                )
                logger.info("成功创建嵌套块")
                return result
            except Exception as e:
                logger.error(f"创建嵌套块失败: {str(e)}")
                raise

        @self.mcp.tool()
        async def upload_media(
            file_name: str,
            parent_type: str,
            parent_node: str,
            file_content: bytes,
            size: int,
            checksum: Optional[str] = None,
            extra: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            上传媒体文件

            通过飞书API上传媒体文件到云文档。

            Args:
                file_name: 文件名，最大长度250字符
                parent_type: 上传点类型，可选值：doc_image/docx_image/sheet_image/doc_file/docx_file
                parent_node: 上传点token（目标云文档token）
                file_content: 文件的二进制内容
                size: 文件大小（字节），最大20MB
                checksum: 可选，文件的Adler-32校验和
                extra: 可选，额外信息，格式：{"drive_route_token":"文档token"}

            Returns:
                包含上传结果的字典：
                - file_token: 上传文件的token

            Raises:
                ValueError: 当headers中缺少必要的认证信息或参数无效
                RuntimeError: 当API调用失败
            """
            logger.info(f"上传媒体文件: file_name={file_name}, parent_type={parent_type}")
            try:
                result = await self.upload_all.upload_media(
                    file_name, parent_type, parent_node, file_content, size, checksum, extra
                )
                logger.info("成功上传媒体文件")
                return result
            except Exception as e:
                logger.error(f"上传媒体文件失败: {str(e)}")
                raise

        @self.mcp.tool()
        async def batch_update_blocks(
            document_id: str,
            requests: list,
            document_revision_id: int = -1,
            client_token: Optional[str] = None,
            user_id_type: str = "open_id"
        ) -> Dict[str, Any]:
            """
            批量更新文档块

            通过飞书API批量更新文档块的内容，支持文本元素、样式、表格等操作。

            Args:
                document_id: 文档ID
                requests: 更新请求列表，每个请求包含block_id和具体的更新操作
                document_revision_id: 文档版本ID（默认-1表示最新版本）
                client_token: 可选的UUIDv4，用于幂等更新
                user_id_type: 用户ID类型，可选值：open_id、union_id、user_id

            Returns:
                包含更新结果的字典：
                - blocks: 更新后的块对象列表
                - client_token: 操作标识符
                - document_revision_id: 新的文档版本ID

            Raises:
                ValueError: 当headers中缺少必要的认证信息或参数无效
                RuntimeError: 当API调用失败
            """
            logger.info(f"批量更新文档块: document_id={document_id}, requests_count={len(requests)}")
            try:
                result = await self.update_blocks.batch_update_blocks(
                    document_id, requests, document_revision_id, client_token, user_id_type
                )
                logger.info("成功批量更新文档块")
                return result
            except Exception as e:
                logger.error(f"批量更新文档块失败: {str(e)}")
                raise

        @self.mcp.tool()
        async def add_permission_member(
            token: str,
            doc_type: str,
            member_type: str,
            member_id: str,
            perm: str,
            perm_type: Optional[str] = None,
            collaborator_type: Optional[str] = None,
            need_notification: Optional[bool] = None
        ) -> Dict[str, Any]:
            """
            为指定云文档添加协作者
            
            通过飞书API为指定云文档添加协作者，支持用户、群组、部门等多种协作者类型。

            Args:
                token: 云文档的token
                doc_type: 云文档类型，可选值：doc、sheet、file、wiki、bitable、docx、folder、mindnote、minutes、slides
                member_type: 协作者ID类型，可选值：email、openid、unionid、openchat、opendepartmentid、userid、groupid、wikispaceid
                member_id: 协作者ID
                perm: 协作者对应的权限角色，可选值：view、edit、full_access
                perm_type: 协作者的权限角色类型，可选值：container、single_page（仅知识库文档有效）
                collaborator_type: 协作者类型，可选值：user、chat、department、group、wiki_space_member、wiki_space_viewer、wiki_space_editor
                need_notification: 添加权限后是否通知对方（仅user_access_token有效）

            Returns:
                包含添加结果的字典：
                - member: 添加的协作者信息
                - member_type: 协作者ID类型
                - member_id: 协作者ID
                - perm: 权限角色
                - perm_type: 权限角色类型
                - type: 协作者类型

            Raises:
                ValueError: 当参数无效时
                RuntimeError: 当API调用失败时
            """
            logger.info(f"添加协作者权限: token={token}, doc_type={doc_type}, member_type={member_type}, member_id={member_id}, perm={perm}")
            try:
                result = await self.add_permission_member.add_permission_member(
                    token, doc_type, member_type, member_id, perm, perm_type, collaborator_type, need_notification
                )
                logger.info("成功添加协作者权限")
                return result
            except Exception as e:
                logger.error(f"添加协作者权限失败: {str(e)}")
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
        if hasattr(self, 'create_doc'):
            await self.create_doc.close()
        if hasattr(self, 'convert_block'):
            await self.convert_block.close()
        if hasattr(self, 'create_block'):
            await self.create_block.close()
        if hasattr(self, 'upload_all'):
            await self.upload_all.close()
        if hasattr(self, 'add_permission_member'):
            await self.add_permission_member.close()
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