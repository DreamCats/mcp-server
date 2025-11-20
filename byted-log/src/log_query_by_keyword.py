"""
根据 psm 名称、指定区域、时间范围、关键词过滤条件，查询符合条件的日志数据。

"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

# 获取日志记录器实例
logger = structlog.get_logger(__name__)

class LogQueryByKeyword:
    """
    多区域日志发现器

    提供基于 JWT 认证的多区域日志查询功能，支持美区和国际化区域的并发查询。
    """

    # 区域配置信息
    # 定义不同区域的日志服务配置，包括 URL、显示名称、可用区域和默认虚拟区域
    REGION_CONFIGS = {
        "us": {
            "url": "https://logservice-tx.tiktok-us.org/streamlog/platform/microservice/v2/query/log",
            "display_name": "美区",
            "zones": ["US-TTP", "US-TTP2"],  # 美区可用区域
            "default_vregion": "US-TTP,US-TTP2"  # 默认虚拟区域
        },
        "i18n": {
            "url": "https://logservice-sg.tiktok-row.org/streamlog/platform/microservice/v2/query/log",
            "display_name": "国际化区域（新加坡）",
            "zones": ["Singapore-Common", "US-East", "Singapore-Central"],  # 国际化区域可用区域
            "default_vregion": "Singapore-Common,US-East,Singapore-Central"  # 默认虚拟区域
        }
    }

    def __init__(self, jwt_managers: Dict[str, Any]):
        """
        初始化日志发现器

        使用多区域 JWT 管理器初始化日志发现器，配置 HTTP 客户端。

        参数:
            jwt_managers: 区域 JWT 管理器字典，将区域键映射到 JWTAuthManager 实例
                         期望的键: "us", "i18n"（如果需要也可以包含 "cn"）
        """
        # 保存 JWT 管理器实例
        self.jwt_managers = jwt_managers

        # 配置 HTTP 客户端
        # 设置超时时间和请求头，模拟浏览器行为以避免被拦截
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30秒超时
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/json",
            }
        )

    async def query_logs_by_keyword(self, region: str, psm_list: Optional[List[str]] = None,
                                  start_time: Optional[int] = None, end_time: Optional[int] = None,
                                  keyword_filter_include: Optional[List[str]] = None,
                                  keyword_filter_exclude: Optional[List[str]] = None,
                                  limit: int = 100, vregion: Optional[str] = None) -> Dict[str, Any]:
        """
        根据关键词和时间范围查询日志

        根据提供的PSM列表、时间范围、关键词过滤条件，在指定区域查询符合条件的日志数据。

        参数:
            region: 目标区域 - "us"（美区）、"i18n"（国际化区域）
            psm_list: PSM服务列表用于过滤（可选）
            start_time: 开始时间戳（秒级，可选，默认当前时间-1小时）
            end_time: 结束时间戳（秒级，可选，默认当前时间）
            keyword_filter_include: 包含关键词列表（可选）
            keyword_filter_exclude: 排除关键词列表（可选）
            limit: 返回结果数量限制（默认：100）
            vregion: 虚拟区域（可选，使用默认配置）

        返回:
            日志查询结果，包含日志内容列表

        异常:
            RuntimeError: 如果日志查询失败
            ValueError: 如果区域参数无效
        """
        logger.info("开始关键词查询日志", region=region, psm_list=psm_list,
                   start_time=start_time, end_time=end_time,
                   keyword_filter_include=keyword_filter_include,
                   keyword_filter_exclude=keyword_filter_exclude, limit=limit)

        # 验证区域参数有效性
        if region not in self.REGION_CONFIGS:
            raise ValueError(f"无效的区域参数: {region}。支持的区域: {list(self.REGION_CONFIGS.keys())}")

        # 只查询指定区域
        return await self.query_single_region_by_keyword(
            region, psm_list, start_time, end_time,
            keyword_filter_include, keyword_filter_exclude, limit, vregion
        )

    async def query_single_region_by_keyword(self, region_key: str, psm_list: Optional[List[str]] = None,
                                           start_time: Optional[int] = None, end_time: Optional[int] = None,
                                           keyword_filter_include: Optional[List[str]] = None,
                                           keyword_filter_exclude: Optional[List[str]] = None,
                                           limit: int = 100, vregion: Optional[str] = None) -> Dict[str, Any]:
        """
        查询单个区域的日志（基于关键词过滤）

        在指定的单个区域中基于关键词和时间范围查询日志信息。

        参数:
            region_key: 区域键，来自 REGION_CONFIGS 配置
            psm_list: PSM服务列表用于过滤（可选）
            start_time: 开始时间戳（秒级）
            end_time: 结束时间戳（秒级）
            keyword_filter_include: 包含关键词列表
            keyword_filter_exclude: 排除关键词列表
            limit: 返回结果数量限制
            vregion: 虚拟区域（可选）

        返回:
            日志查询结果
        """
        # 获取区域配置信息
        config = self.REGION_CONFIGS[region_key]
        region_url = config["url"]

        # 设置默认时间范围（如果未提供）
        current_time = int(datetime.now().timestamp())
        if not end_time:
            end_time = current_time
        if not start_time:
            start_time = end_time - 3600  # 默认1小时前

        # 设置默认虚拟区域
        if not vregion:
            vregion = config["default_vregion"]  # 使用默认区域

        # 记录查询日志
        logger.info("开始查询单个区域（关键词）", region=region_key, start_time=start_time,
                   end_time=end_time, vregion=vregion, psm_count=len(psm_list) if psm_list else 0)

        # 获取特定区域的JWT令牌
        jwt_manager = self.jwt_managers.get(region_key)
        if not jwt_manager:
            logger.error(f"未配置JWT管理器用于区域: {region_key}")
            raise RuntimeError(f"未配置JWT管理器用于区域: {region_key}")

        # 异步获取JWT令牌
        jwt_token = await jwt_manager.get_jwt_token()

        # 构建关键词过滤条件
        keyword_filter = self._build_keyword_filter(keyword_filter_include, keyword_filter_exclude)

        # 准备请求体（基于诉求中的例子）
        request_body = {
            "data_source_uid": "",
            "context": [],
            "start": start_time,
            "end": end_time,
            "psm_list": psm_list if psm_list else [],
            "keyword_filter": keyword_filter,
            "enable_index": False,
            "limit": limit,
            "timeout_in_ms": 2000,
            "vregion": vregion
        }

        # 准备请求头
        headers = {
            "X-Jwt-Token": jwt_token,  # JWT认证令牌
            "accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
        }

        try:
            # 发送HTTP POST请求到日志服务API
            response = await self.client.post(region_url, headers=headers, json=request_body)
            response.raise_for_status()  # 检查HTTP状态码

            # 解析响应数据
            data = response.json()

            # 格式化响应结果，包含区域信息
            result = {
                "region": region_key,
                "region_display_name": config["display_name"],
                "start_time": start_time,
                "end_time": end_time,
                "vregion": vregion,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            # 统计日志条目数量
            content_count = len(data.get("data", {}).get("content", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("关键词日志查询完成", region=region_key, content_count=content_count,
                       status_code=response.status_code, start_time=start_time, end_time=end_time)
            return result

        except httpx.TimeoutException:
            # 处理超时异常
            logger.warning("关键词日志查询超时", region=region_key, start_time=start_time, end_time=end_time)
            raise RuntimeError(f"查询日志超时，区域: {region_key}，时间范围: {start_time}-{end_time}")

        except httpx.HTTPError as e:
            # 处理HTTP错误
            logger.error("关键词日志查询HTTP错误", region=region_key, start_time=start_time, end_time=end_time,
                        error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"查询日志HTTP错误，区域: {region_key}，时间范围: {start_time}-{end_time}: {e}")

        except Exception as e:
            # 处理其他异常
            logger.error("关键词日志查询意外错误", region=region_key, start_time=start_time, end_time=end_time,
                        error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"查询日志意外错误，区域: {region_key}，时间范围: {start_time}-{end_time}: {e}")

    def _build_keyword_filter(self, include_keywords: Optional[List[str]], exclude_keywords: Optional[List[str]]) -> Dict[str, Any]:
        """
        构建关键词过滤条件

        根据包含和排除关键词列表构建符合API要求的关键词过滤条件。

        参数:
            include_keywords: 包含关键词列表
            exclude_keywords: 排除关键词列表

        返回:
            关键词过滤条件字典
        """
        keyword_filter = {
            "include": {
                "case_sensitive": True,
                "operator": "AND",
                "word_list": []
            },
            "exclude": {
                "words": [],
                "case_sensitive": True,
                "operator": "AND"
            }
        }

        # 处理包含关键词
        if include_keywords:
            for keyword in include_keywords:
                keyword_filter["include"]["word_list"].append({
                    "word": keyword,
                    "is_term": False
                })
        else:
            # 如果没有包含关键词，设置空条件
            keyword_filter["include"]["word_list"] = []

        # 处理排除关键词
        if exclude_keywords:
            keyword_filter["exclude"]["words"] = exclude_keywords
        else:
            keyword_filter["exclude"]["words"] = []

        return keyword_filter

    def extract_log_messages_v2(self, log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从v2/log API响应中提取日志消息

        解析日志服务返回的v2版本数据，提取关键的日志消息信息。
        重点关注_msg字段，同时提取其他有用的元数据。

        参数:
            log_data: 来自v2/log API响应的原始日志数据

        返回:
            提取的日志消息列表，包含关键信息
        """
        messages = []  # 存储提取的日志消息

        # 验证数据格式
        if not isinstance(log_data, dict) or "data" not in log_data:
            return messages

        # 获取数据内容
        data = log_data.get("data", {})
        content = data.get("content", [])  # 日志内容列表

        # 遍历每个内容项
        for content_item in content:
            if not isinstance(content_item, dict):
                continue

            # 提取上下文ID
            context_id = content_item.get("context_id", "")
            messages_list = content_item.get("messages", [])

            # 创建消息字典来存储所有字段
            message_data = {
                "context_id": context_id,
                "fields": {},
                "msg_content": ""
            }

            # 提取所有字段
            for msg in messages_list:
                if not isinstance(msg, dict):
                    continue

                key = msg.get("key", "")
                value = msg.get("value", "")

                # 存储字段信息
                message_data["fields"][key] = {
                    "value": value,
                    "type": msg.get("type", ""),
                    "biz_type": msg.get("biz_type", ""),
                    "highlight": msg.get("highlight", False)
                }

                # 特别关注_msg字段
                if key == "_msg":
                    message_data["msg_content"] = value

            # 只包含有内容的日志消息
            if message_data["fields"]:
                messages.append(message_data)

        return messages

    def _get_field_value(self, fields: Dict[str, Any], field_key: str) -> str:
        """
        从字段字典中获取指定字段的值

        参数:
            fields: 字段字典
            field_key: 字段键名

        返回:
            字段值，如果不存在返回空字符串
        """
        field_info = fields.get(field_key, {})
        return field_info.get("value", "")

    async def get_log_details_by_keyword(self, region: str, psm_list: Optional[List[str]] = None,
                                       start_time: Optional[int] = None, end_time: Optional[int] = None,
                                       keyword_filter_include: Optional[List[str]] = None,
                                       keyword_filter_exclude: Optional[List[str]] = None,
                                       limit: int = 100, vregion: Optional[str] = None) -> Dict[str, Any]:
        """
        获取基于关键词过滤的详细日志信息

        查询日志并提取详细的消息内容，包括元数据和统计信息。

        参数:
            region: 目标区域
            psm_list: PSM服务列表用于过滤（可选）
            start_time: 开始时间戳（秒级）
            end_time: 结束时间戳（秒级）
            keyword_filter_include: 包含关键词列表
            keyword_filter_exclude: 排除关键词列表
            limit: 返回结果数量限制
            vregion: 虚拟区域（可选）

        返回:
            包含提取消息的详细日志信息和统计
        """
        # 查询日志数据
        result = await self.query_logs_by_keyword(region, psm_list, start_time, end_time,
                                                keyword_filter_include, keyword_filter_exclude, limit, vregion)

        # 获取数据内容
        data = result.get("data", {})

        # 提取日志消息
        messages = self.extract_log_messages_v2(data)

        # 获取查询统计信息
        total_log_size = data.get("log_size", 0)
        finished = data.get("finished", False)
        total_scan_log_size = data.get("total_scan_log_size", 0)
        query_progress = data.get("query_progress", 0)

        # 返回结构化的日志详细信息
        return {
            "region": result.get("region", "unknown"),
            "region_display_name": result.get("region_display_name", "未知区域"),
            "start_time": result.get("start_time"),
            "end_time": result.get("end_time"),
            "vregion": result.get("vregion", "unknown"),
            "messages": messages,
            "total_messages": len(messages),
            "statistics": {
                "log_size": total_log_size,
                "finished": finished,
                "total_scan_log_size": total_scan_log_size,
                "query_progress": query_progress
            },
            "timestamp": result.get("timestamp", "Unknown")
        }

    def format_log_response_by_keyword(self, log_details: Dict[str, Any]) -> str:
        """
        格式化基于关键词的日志查询结果为可读响应

        将详细的日志信息格式化为用户友好的字符串响应，包含区域信息、时间范围和消息详情。

        参数:
            log_details: 详细的日志信息（来自get_log_details_by_keyword）

        返回:
            格式化的字符串响应
        """
        # 提取日志详情信息
        messages = log_details.get("messages", [])
        total_messages = log_details.get("total_messages", 0)
        region = log_details.get("region", "unknown")
        region_display_name = log_details.get("region_display_name", "未知区域")
        start_time = log_details.get("start_time", 0)
        end_time = log_details.get("end_time", 0)
        vregion = log_details.get("vregion", "unknown")
        statistics = log_details.get("statistics", {})

        # 格式化时间戳
        start_time_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S") if start_time else "未知"
        end_time_str = datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S") if end_time else "未知"

        # 构建响应字符串
        response = f"""
🔍 **关键词日志查询结果**
🌍 **查询区域**: {region_display_name} ({region})
📍 **虚拟区域**: {vregion}
⏰ **时间范围**: {start_time_str} 到 {end_time_str}
📊 **匹配日志数**: {total_messages}
📈 **查询进度**: {statistics.get('query_progress', 0)}%
💾 **扫描日志大小**: {self._format_bytes(statistics.get('total_scan_log_size', 0))}
"""

        # 添加日志消息详情
        if messages:
            response += f"\n📝 **日志消息详情** (显示前{min(total_messages, 10)}条，共{total_messages}条):\n"

            # 只显示前10条消息，避免输出过长
            for i, message in enumerate(messages[:10], 1):
                context_id = message.get("context_id", "")
                msg_content = message.get("msg_content", "")
                fields = message.get("fields", {})

                response += f"\n--- 日志 {i} ---\n"
                response += f"  🆔 **上下文ID**: {context_id}\n"

                # 提取关键字段
                level = self._get_field_value(fields, "_level")
                logid = self._get_field_value(fields, "__logid")
                psm = self._get_field_value(fields, "_psm")
                podname = self._get_field_value(fields, "_podname")
                timestamp = self._get_field_value(fields, "__timestamp")
                idc = self._get_field_value(fields, "_idc")
                ipv4 = self._get_field_value(fields, "_ipv4")

                if level:
                    response += f"  📊 **级别**: {level}\n"
                if logid:
                    response += f"  🆔 **日志ID**: {logid}\n"
                if psm:
                    response += f"  🏷️ **PSM**: {psm}\n"
                if podname:
                    response += f"  🐳 **Pod**: {podname}\n"
                if idc:
                    response += f"  🏢 **IDC**: {idc}\n"
                if ipv4:
                    response += f"  🌐 **IP地址**: {ipv4}\n"
                if timestamp:
                    # 转换微秒时间戳为可读格式
                    try:
                        ts_seconds = int(timestamp) / 1000000  # 微秒转秒
                        time_str = datetime.fromtimestamp(ts_seconds).strftime("%Y-%m-%d %H:%M:%S")
                        response += f"  ⏰ **时间**: {time_str}\n"
                    except (ValueError, TypeError):
                        pass

                # 添加消息内容（如果存在）
                if msg_content:
                    response += f"  💬 **消息内容**: {msg_content[:200]}"
                    if len(msg_content) > 200:
                        response += "... (内容已截断)"
                    response += "\n"

                # 检查是否有高亮字段
                highlighted_fields = [k for k, v in fields.items() if v.get("highlight", False)]
                if highlighted_fields:
                    response += f"  ✨ **高亮字段**: {', '.join(highlighted_fields)}\n"

            # 如果还有更多消息，提示用户
            if total_messages > 10:
                response += f"\n💡 **提示**: 还有 {total_messages - 10} 条日志未显示，可通过调整limit参数查看更多\n"

        else:
            response += "\n❌ **未找到匹配的日志消息**\n"
            response += "💡 **建议**: \n"
            response += "  - 检查关键词拼写是否正确\n"
            response += "  - 扩大时间范围\n"
            response += "  - 检查PSM服务名称是否正确\n"
            response += "  - 尝试不同的虚拟区域\n"

        # 添加查询时间戳
        response += f"\n⏰ **查询时间**: {log_details.get('timestamp', '未知')}"

        return response.strip()

    def _format_bytes(self, bytes_count: int) -> str:
        """
        格式化字节数为人类可读格式

        参数:
            bytes_count: 字节数

        返回:
            格式化的字符串
        """
        if bytes_count == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0

        return f"{bytes_count:.1f} PB"

    async def close(self):
        """
        关闭 HTTP 客户端和所有 JWT 管理器

        清理资源，关闭 HTTP 连接和所有的 JWT 认证管理器。
        """
        # 关闭 HTTP 客户端连接
        await self.client.aclose()

        # 关闭所有 JWT 管理器
        for jwt_manager in self.jwt_managers.values():
            await jwt_manager.close()

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