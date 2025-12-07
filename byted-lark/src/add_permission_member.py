"""
字节跳动 Lark MCP 服务器 - 添加协作者权限模块

本模块处理为指定云文档添加协作者的API调用，支持用户、群组、部门等多种协作者类型。
"""

import httpx
import structlog
from typing import Dict, Any, Optional

# 获取日志记录器实例
logger = structlog.get_logger(__name__)


class AddPermissionMember:
    """
    添加协作者权限管理器
    
    提供为指定云文档添加协作者的功能，支持多种协作者类型和权限级别。
    """

    def __init__(self, auth_manager):
        """
        初始化添加协作者权限管理器
        
        Args:
            auth_manager: 认证管理器实例，用于获取访问令牌
        """
        self.auth = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)

    async def add_permission_member(
        self,
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
        
        # 验证必需参数
        if not token:
            raise ValueError("token参数不能为空")
        if not doc_type:
            raise ValueError("doc_type参数不能为空")
        if not member_type:
            raise ValueError("member_type参数不能为空")
        if not member_id:
            raise ValueError("member_id参数不能为空")
        if not perm:
            raise ValueError("perm参数不能为空")
            
        # 验证doc_type是否有效
        valid_doc_types = ["doc", "sheet", "file", "wiki", "bitable", "docx", "folder", "mindnote", "minutes", "slides"]
        if doc_type not in valid_doc_types:
            raise ValueError(f"无效的doc_type参数，支持的值：{', '.join(valid_doc_types)}")
            
        # 验证member_type是否有效
        valid_member_types = ["email", "openid", "unionid", "openchat", "opendepartmentid", "userid", "groupid", "wikispaceid"]
        if member_type not in valid_member_types:
            raise ValueError(f"无效的member_type参数，支持的值：{', '.join(valid_member_types)}")
            
        # 验证perm是否有效
        valid_perms = ["view", "edit", "full_access"]
        if perm not in valid_perms:
            raise ValueError(f"无效的perm参数，支持的值：{', '.join(valid_perms)}")
            
        # 验证perm_type（如果提供）
        if perm_type:
            valid_perm_types = ["container", "single_page"]
            if perm_type not in valid_perm_types:
                raise ValueError(f"无效的perm_type参数，支持的值：{', '.join(valid_perm_types)}")
                
        # 验证collaborator_type（如果提供）
        if collaborator_type:
            valid_types = ["user", "chat", "department", "group", "wiki_space_member", "wiki_space_viewer", "wiki_space_editor"]
            if collaborator_type not in valid_types:
                raise ValueError(f"无效的type参数，支持的值：{', '.join(valid_types)}")

        try:
            # 获取访问令牌
            access_token = await self.auth.get_tenant_access_token()
            
            # 构建请求URL
            url = f"https://open.larkoffice.com/open-apis/drive/v1/permissions/{token}/members"
            
            # 构建查询参数
            params = {"type": doc_type}
            if need_notification is not None:
                params["need_notification"] = str(need_notification).lower()
                
            # 构建请求体
            request_body = {
                "member_type": member_type,
                "member_id": member_id,
                "perm": perm
            }
            
            # 添加可选参数
            if perm_type:
                request_body["perm_type"] = perm_type
            if collaborator_type:
                request_body["type"] = collaborator_type
                
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=utf-8"
            }
            
            # 发送请求
            response = await self.client.post(
                url,
                headers=headers,
                params=params,
                json=request_body
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                raise RuntimeError(f"添加协作者权限失败: {error_msg}")
                
            logger.info("成功添加协作者权限")
            return result.get("data", {})
            
        except httpx.HTTPError as e:
            logger.error(f"添加协作者权限时发生HTTP错误: {str(e)}")
            raise RuntimeError(f"添加协作者权限失败: {e}")
        except Exception as e:
            logger.error(f"添加协作者权限时发生意外错误: {str(e)}")
            raise

    async def close(self):
        """
        关闭HTTP客户端
        
        释放HTTP客户端连接资源。
        """
        await self.client.aclose()

    def __del__(self):
        """
        对象销毁时的清理工作
        
        在对象被垃圾回收时尝试关闭HTTP客户端连接。
        """
        try:
            if hasattr(self, 'client'):
                import asyncio
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.client.aclose())
        except Exception:
            pass