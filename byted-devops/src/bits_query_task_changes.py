"""
字节跳动 MCP 服务器 Bits 查询模块

本模块处理 Bits 平台的开发任务、代码评审和变更查询功能。
支持通过 devBasicId 查询相关的开发任务、代码变更、评审状态等信息。
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import structlog

# 获取日志记录器实例
logger = structlog.get_logger(__name__)


class BitsQueryForTaskChanges:
    """
    Bits 平台查询器

    提供基于 JWT 认证的 Bits 平台开发任务和代码变更查询功能。
    该类封装了 Bits API 的调用，提供统一的任务查询接口。
    """

    # Bits API 配置
    BITS_API_CONFIG = {
        "url": "https://bits.bytedance.net/api/v1/dev/task/changes",
        "display_name": "Bits 平台"
    }

    def __init__(self, jwt_manager: Any):
        """
        初始化 Bits 查询器

        使用 JWT 管理器初始化 Bits 查询器，配置 HTTP 客户端。

        参数:
            jwt_manager: JWT 认证管理器实例
        """
        # 保存 JWT 管理器实例
        self.jwt_manager = jwt_manager

        # 配置 HTTP 客户端
        # 设置超时时间和请求头，模拟浏览器行为以避免被拦截
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30秒超时
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                # "Accept-Encoding": "gzip, deflate, br, zstd",
                "Content-Type": "application/json",
            }
        )

    async def query_task_changes(self, dev_basic_id: int) -> Dict[str, Any]:
        """
        查询开发任务变更信息

        根据 devBasicId 查询相关的开发任务、代码变更、评审状态等信息。

        参数:
            dev_basic_id: 开发任务基础 ID

        返回:
            Bits API 响应数据，包含任务变更列表

        异常:
            RuntimeError: 如果查询失败
            ValueError: 如果参数无效
        """
        logger.info("开始查询 Bits 任务变更", dev_basic_id=dev_basic_id)

        # 验证参数
        if not isinstance(dev_basic_id, int) or dev_basic_id <= 0:
            raise ValueError(f"无效的 devBasicId: {dev_basic_id}")

        # 获取 JWT 令牌
        jwt_token = await self.jwt_manager.get_jwt_token()

        # 准备请求参数
        params = {
            "devBasicId": dev_basic_id
        }

        # 准备请求头
        headers = {
            "x-jwt-token": jwt_token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

        try:
            # 发送 HTTP GET 请求到 Bits API
            response = await self.client.get(
                self.BITS_API_CONFIG["url"],
                params=params,
                headers=headers
            )

            response.raise_for_status()  # 检查 HTTP 状态码

            data = response.json()                

            # 验证响应格式
            if not isinstance(data, dict):
                raise ValueError("无效的响应格式")

            # 记录查询结果
            change_list = data.get("data", {}).get("changeList", [])
            logger.info("Bits 任务查询完成",
                       dev_basic_id=dev_basic_id,
                       change_count=len(change_list),
                       status_code=response.status_code)

            return data

        except httpx.TimeoutException:
            # 处理超时异常
            logger.warning("Bits 查询超时", dev_basic_id=dev_basic_id)
            raise RuntimeError(f"查询 Bits 任务超时，devBasicId: {dev_basic_id}")

        except httpx.HTTPError as e:
            # 处理 HTTP 错误
            logger.error("Bits 查询 HTTP 错误",
                        dev_basic_id=dev_basic_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise RuntimeError(f"查询 Bits 任务 HTTP 错误，devBasicId: {dev_basic_id}: {e}")

        except Exception as e:
            # 处理其他异常
            logger.error("Bits 查询意外错误",
                        dev_basic_id=dev_basic_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise RuntimeError(f"查询 Bits 任务意外错误，devBasicId: {dev_basic_id}: {e}")

    def extract_task_info(self, bits_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 Bits API 响应中提取任务信息

        解析 Bits API 返回的原始数据，提取关键的开发任务和代码变更信息。
        重点关注 changeList、changes、代码元素等关键字段。

        参数:
            bits_data: 来自 Bits API 响应的原始数据

        返回:
            提取的任务信息列表
        """
        tasks = []  # 存储提取的任务信息

        # 验证数据格式
        if not isinstance(bits_data, dict):
            return tasks

        # 获取响应数据
        response_data = bits_data.get("data", {})
        change_list = response_data.get("changeList", [])

        # 遍历每个变更
        for i, change_item in enumerate(change_list):
            if not isinstance(change_item, dict):
                continue

            # 提取变更信息
            change_info = change_item.get("change", {})
            if not change_info:
                continue

            # 提取基本信息
            task_info = {
                "index": i + 1,
                "task_id": change_info.get("id", ""),
                "creator": change_info.get("creator", ""),
                "title": change_info.get("title", ""),
                "status": change_info.get("status", ""),
                "create_time": self._format_timestamp(change_info.get("createAt")),
                "is_draft": change_info.get("isDraft", False),
                "manifest": self._extract_manifest_info(change_info.get("manifest", {})),
                "diff_count": change_item.get("diffCount", {}),
                "comment_count": change_item.get("commentCount", 0),
                "review_info": self._extract_review_info(change_item.get("reviewInfo", {})),
                "state_info": change_item.get("stateInfo", {}),
                "merge_rule": change_item.get("mergeRule", {})
            }

            tasks.append(task_info)

        return tasks

    def _extract_manifest_info(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取代码变更清单信息

        参数:
            manifest: 代码变更清单数据

        返回:
            提取的清单信息
        """
        if not isinstance(manifest, dict):
            return {}

        code_element = manifest.get("codeElement", {})
        if not code_element:
            return {}

        return {
            "repository": code_element.get("repoPath", ""),
            "source_branch": code_element.get("sourceBranch", ""),
            "target_branch": code_element.get("targetBranch", ""),
            "mr_title": code_element.get("title", ""),
            "mr_url": code_element.get("url", ""),
            "mr_status": code_element.get("status", ""),
            "mr_creator": code_element.get("creator", ""),
            "hosting_platform": code_element.get("hostingPlatform", ""),
            "code_change_id": code_element.get("codeChangeId", ""),
            "repository_id": code_element.get("repoId", ""),
            "checkout_from": code_element.get("checkoutFrom", ""),
            "latest_commit": self._extract_commit_info(code_element.get("lastestCommit", {})),
            "codebase_repo_id": code_element.get("codebaseRepoId", ""),
            "mr_iid": code_element.get("iid", ""),
            "codebase_change_id": code_element.get("codebaseChangeId", ""),
            "is_codebase_draft": code_element.get("isCodebaseDraft", False)
        }

    def _extract_commit_info(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取提交信息

        参数:
            commit: 提交信息数据

        返回:
            提取的提交信息
        """
        if not isinstance(commit, dict):
            return {}

        return {
            "commit_id": commit.get("id", ""),
            "short_id": commit.get("short_id", ""),
            "title": commit.get("title", "").strip()
        }

    def _extract_review_info(self, review_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取评审信息

        参数:
            review_info: 评审信息数据

        返回:
            提取的评审信息
        """
        if not isinstance(review_info, dict):
            return {}

        reviewers_info = review_info.get("reviewersInfo", [])
        review_status = review_info.get("reviewStatus", "")
        reviewer_count = review_info.get("reviewerCount", {})
        review_rules = review_info.get("reviewRules", {})

        return {
            "review_status": review_status,
            "total_reviewers": reviewer_count.get("total", 0),
            "pass_number": reviewer_count.get("passNumber", 0),
            "rejection_number": reviewer_count.get("rejectionNumber", 0),
            "reviewers": [
                {
                    "username": reviewer.get("username", ""),
                    "status": reviewer.get("status", "")
                }
                for reviewer in reviewers_info if isinstance(reviewer, dict)
            ],
            "review_rules": review_rules
        }

    def _format_timestamp(self, timestamp: Any) -> str:
        """
        格式化时间戳

        参数:
            timestamp: 时间戳（毫秒）

        返回:
            格式化的时间字符串
        """
        if not timestamp or not isinstance(timestamp, (int, float)):
            return "未知"

        try:
            # 将毫秒时间戳转换为秒
            timestamp_seconds = timestamp / 1000
            dt = datetime.fromtimestamp(timestamp_seconds)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "未知"

    async def get_task_details(self, dev_basic_id: int) -> Dict[str, Any]:
        """
        获取开发任务的详细信息

        查询 Bits 任务并提取详细的变更信息，包括代码评审状态、
        代码变更详情、评审者信息等。

        参数:
            dev_basic_id: 开发任务基础 ID

        返回:
            包含提取任务信息的详细数据
        """
        # 查询 Bits 数据
        result = await self.query_task_changes(dev_basic_id)

        # 提取任务信息
        tasks = self.extract_task_info(result)

        # 获取响应元数据
        code = result.get("code", 0)
        message = result.get("message", "")

        # 返回结构化的任务详细信息
        return {
            "dev_basic_id": dev_basic_id,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "api_code": code,
            "api_message": message,
            "timestamp": datetime.now().isoformat(),
            "platform": self.BITS_API_CONFIG["display_name"]
        }

    def format_task_response(self, task_details: Dict[str, Any]) -> str:
        """
        格式化任务详情为可读响应

        将详细的任务信息格式化为用户友好的字符串响应，
        包含任务基本信息、代码变更详情、评审状态等。

        参数:
            task_details: 详细的任务信息

        返回:
            格式化的字符串响应
        """
        # 提取任务详情信息
        tasks = task_details.get("tasks", [])
        total_tasks = task_details.get("total_tasks", 0)
        dev_basic_id = task_details.get("dev_basic_id", "Unknown")
        api_message = task_details.get("api_message", "")
        platform = task_details.get("platform", "Bits 平台")

        # 构建响应字符串
        response = f"""
📋 **Bits 任务查询结果**
🔍 **开发任务 ID**: {dev_basic_id}
🏢 **查询平台**: {platform}
📊 **任务总数**: {total_tasks}
"""

        # 添加 API 状态信息
        if api_message:
            response += f"✅ **API 状态**: {api_message}\n"

        # 添加任务详情
        if tasks:
            response += "\n📝 **任务详情**:\n"
            for i, task in enumerate(tasks, 1):
                response += f"\n{'='*60}\n"
                response += f"**任务 {i}**\n"
                response += f"🆔 **任务 ID**: {task.get('task_id', '未知')}\n"
                response += f"👤 **创建者**: {task.get('creator', '未知')}\n"
                response += f"📋 **标题**: {task.get('title', '未知')}\n"
                response += f"📊 **状态**: {task.get('status', '未知')}\n"
                response += f"⏰ **创建时间**: {task.get('create_time', '未知')}\n"
                response += f"📝 **评论数**: {task.get('comment_count', 0)}\n"

                # 添加代码变更信息
                manifest = task.get('manifest', {})
                if manifest:
                    response += f"\n💻 **代码变更信息**:\n"
                    response += f"  📁 **仓库**: {manifest.get('repository', '未知')}\n"
                    response += f"  🌿 **源分支**: {manifest.get('source_branch', '未知')}\n"
                    response += f"  🎯 **目标分支**: {manifest.get('target_branch', '未知')}\n"
                    response += f"  📝 **MR 标题**: {manifest.get('mr_title', '未知')}\n"
                    response += f"  🔗 **MR 链接**: {manifest.get('mr_url', '未知')}\n"
                    response += f"  📊 **MR 状态**: {manifest.get('mr_status', '未知')}\n"

                    # 添加最新提交信息
                    latest_commit = manifest.get('latest_commit', {})
                    if latest_commit:
                        response += f"  💾 **最新提交**:\n"
                        response += f"    🔑 **提交 ID**: {latest_commit.get('commit_id', '未知')}\n"
                        response += f"    📋 **提交标题**: {latest_commit.get('title', '未知')}\n"

                # 添加代码统计信息
                diff_count = task.get('diff_count', {})
                if diff_count:
                    response += f"\n📈 **代码变更统计**:\n"
                    response += f"  ➕ **新增行数**: {diff_count.get('insertions', 0)}\n"
                    response += f"  ➖ **删除行数**: {diff_count.get('deletions', 0)}\n"

                # 添加评审信息
                review_info = task.get('review_info', {})
                if review_info:
                    response += f"\n👥 **评审信息**:\n"
                    response += f"  📊 **评审状态**: {review_info.get('review_status', '未知')}\n"
                    response += f"  👥 **总评审者**: {review_info.get('total_reviewers', 0)}\n"
                    response += f"  ✅ **通过数**: {review_info.get('pass_number', 0)}\n"
                    response += f"  ❌ **拒绝数**: {review_info.get('rejection_number', 0)}\n"

                    # 添加评审者列表
                    reviewers = review_info.get('reviewers', [])
                    if reviewers:
                        response += f"  📋 **评审者列表**:\n"
                        for reviewer in reviewers:
                            response += f"    👤 {reviewer.get('username', '未知')} - {reviewer.get('status', '未知')}\n"
        else:
            response += "\n❌ **未找到任务信息**\n"

        # 添加查询时间戳
        response += f"\n⏰ **查询时间**: {task_details.get('timestamp', '未知')}"

        return response.strip()

    async def close(self):
        """
        关闭 HTTP 客户端

        清理资源，关闭 HTTP 连接。
        """
        # 关闭 HTTP 客户端连接
        await self.client.aclose()

    def __del__(self):
        """
        对象销毁时的清理工作

        在对象被垃圾回收时尝试关闭 HTTP 客户端连接。
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