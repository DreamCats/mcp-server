"""
字节跳动 MCP 服务器日志发现模块

本模块处理多区域（美区 US-TTP 和东南亚 SEA）的日志查询功能，通过 logid 进行日志搜索。
支持并发区域查询和智能区域检测，提供统一的日志查询接口。
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
import structlog
from datetime import datetime

# 获取日志记录器实例
logger = structlog.get_logger(__name__)


class LogQueryByID:
    """
    多区域日志发现器

    提供基于 JWT 认证的多区域日志查询功能，支持美区和国际化区域的并发查询。
    该类封装了日志服务的 API 调用，提供统一的日志查询接口。
    """

    # 区域配置信息
    # 定义不同区域的日志服务配置，包括 URL、显示名称、可用区域和默认虚拟区域
    REGION_CONFIGS = {
        "us": {
            "url": "https://logservice-tx.tiktok-us.org/streamlog/platform/microservice/v1/query/trace",
            "display_name": "美区",
            "zones": ["US-TTP", "US-TTP2"],  # 美区可用区域
            "default_vregion": "US-TTP,US-TTP2"  # 默认虚拟区域
        },
        "i18n": {
            "url": "https://logservice-sg.tiktok-row.org/streamlog/platform/microservice/v1/query/trace",
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

    async def query_logs_by_logid(self, logid: str, region: str, psm_list: Optional[List[str]] = None,
                                scan_time_min: int = 10) -> Dict[str, Any]:
        """
        根据日志 ID 查询日志（支持多区域）

        根据提供的日志 ID，在指定区域或所有区域中查询相关日志信息。
        支持 PSM 服务过滤和时间范围限制。

        参数:
            logid: 要搜索的日志 ID
            region: 目标区域 - "us"（美区）、"i18n"（国际化区域）
            psm_list: PSM 服务列表用于过滤（可选）
            scan_time_min: 扫描时间范围（分钟，默认：10）

        返回:
            日志查询结果，包含消息详情的项目列表

        异常:
            RuntimeError: 如果日志查询失败
            ValueError: 如果区域参数无效
        """
        logger.info("开始查询日志", logid=logid, psm_list=psm_list,
                   scan_time_min=scan_time_min, region=region)

        # 验证区域参数有效性
        if region not in self.REGION_CONFIGS:
            raise ValueError(f"无效的区域参数: {region}。支持的区域: {list(self.REGION_CONFIGS.keys())}")

        # 只查询指定区域
        return await self.query_single_region(region, logid, psm_list, scan_time_min)

    async def query_single_region(self, region_key: str, logid: str, psm_list: Optional[List[str]] = None,
                                  scan_time_min: int = 10) -> Dict[str, Any]:
        """
        查询单个区域的日志

        在指定的单个区域中查询日志信息，使用该区域对应的 JWT 认证。

        参数:
            region_key: 区域键，来自 REGION_CONFIGS 配置
            logid: 要搜索的日志 ID
            psm_list: PSM 服务列表用于过滤（可选）
            scan_time_min: 扫描时间范围（分钟，默认：10）

        返回:
            日志查询结果
        """
        # 获取区域配置信息
        config = self.REGION_CONFIGS[region_key]
        region_url = config["url"]
        default_vregion = config["default_vregion"]

        # 记录查询日志
        logger.info("开始查询单个区域", region=region_key, logid=logid, vregion=default_vregion)

        # 获取特定区域的 JWT 令牌
        jwt_manager = self.jwt_managers.get(region_key)
        if not jwt_manager:
            logger.error(f"未配置 JWT 管理器用于区域: {region_key}")
            raise RuntimeError(f"未配置 JWT 管理器用于区域: {region_key}")

        # 异步获取 JWT 令牌
        jwt_token = await jwt_manager.get_jwt_token()

        # 准备请求体
        request_body = {
            "logid": logid,  # 日志 ID
            "psm_list": psm_list if psm_list else [],  # PSM 列表，如果为空则传空数组
            "scan_span_in_min": scan_time_min,  # 扫描时间跨度（分钟）
            "vregion": default_vregion  # 虚拟区域
        }

        # 准备请求头
        headers = {
            "X-Jwt-Token": jwt_token,  # JWT 认证令牌
            "accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
        }

        try:
            # 发送 HTTP POST 请求到日志服务 API
            response = await self.client.post(region_url, headers=headers, json=request_body)
            response.raise_for_status()  # 检查 HTTP 状态码

            # 解析响应数据
            data = response.json()

            # 格式化响应结果，包含区域信息
            result = {
                "logid": logid,
                "region": region_key,
                "region_display_name": config["display_name"],
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            # 统计日志项目数量
            items_count = len(data.get("data", {}).get("items", [])) if isinstance(data, dict) and "data" in data else 0
            logger.info("日志查询完成", region=region_key, logid=logid,
                       items_found=items_count, status_code=response.status_code)
            return result

        except httpx.TimeoutException:
            # 处理超时异常
            logger.warning("日志查询超时", region=region_key, logid=logid)
            raise RuntimeError(f"查询日志超时，日志ID: {logid}，区域: {region_key}")

        except httpx.HTTPError as e:
            # 处理 HTTP 错误
            logger.error("日志查询 HTTP 错误", region=region_key, logid=logid,
                        error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"查询日志 HTTP 错误，日志ID: {logid}，区域: {region_key}: {e}")

        except Exception as e:
            # 处理其他异常
            logger.error("日志查询意外错误", region=region_key, logid=logid,
                        error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"查询日志意外错误，日志ID: {logid}，区域: {region_key}: {e}")

    def extract_log_messages(self, log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 API 响应中提取日志消息

        解析日志服务返回的原始数据，提取关键的日志消息信息。
        重点关注 _msg 字段，这是日志的主要内容字段。

        参数:
            log_data: 来自 API 响应的原始日志数据

        返回:
            提取的日志消息列表，包含关键信息
        """
        messages = []  # 存储提取的日志消息

        # 验证数据格式
        if not isinstance(log_data, dict) or "data" not in log_data:
            return messages

        # 获取数据内容
        data = log_data.get("data", {})
        items = data.get("items", [])  # 日志项目列表

        # 遍历每个日志项目
        for item in items:
            if not isinstance(item, dict):
                continue  # 跳过非字典格式的项目

            # 提取基本的项目信息
            item_info = {
                "id": item.get("id", ""),  # 项目 ID
                "group": item.get("group", {}),  # 分组信息（包含 PSM、Pod 等）
                "values": []  # 存储提取的值
            }

            # 从 kv_list 中提取值
            values = item.get("value", [])
            for value in values:
                if not isinstance(value, dict):
                    continue

                kv_list = value.get("kv_list", [])  # 键值对列表
                for kv in kv_list:
                    if not isinstance(kv, dict):
                        continue

                    key = kv.get("key", "")  # 键
                    value_str = kv.get("value", "")  # 值

                    # 重点关注 _msg 字段（日志消息内容）
                    if key == "_msg":
                        item_info["values"].append({
                            "key": key,
                            "value": value_str,
                            "type": kv.get("type", ""),  # 值类型
                            "highlight": kv.get("highlight", False)  # 是否高亮显示
                        })

            # 只包含有 _msg 值的项目
            if item_info["values"]:
                messages.append(item_info)

        return messages

    async def get_log_details(self, logid: str, region:str, psm_list: Optional[List[str]] = None,
                            scan_time_min: int = 10) -> Dict[str, Any]:
        """
        获取特定日志 ID 的详细日志信息

        查询日志并提取详细的消息内容，包括元数据和标签信息。

        参数:
            logid: 要搜索的日志 ID
            psm_list: PSM 服务列表用于过滤（可选）
            scan_time_min: 扫描时间范围（分钟，默认：10）
            region: 目标区域（默认："all"）

        返回:
            包含提取消息的详细日志信息
        """
        # 查询日志数据
        result = await self.query_logs_by_logid(logid, region, psm_list, scan_time_min)

        # 获取数据内容
        data = result.get("data", {})

        # 提取日志消息
        messages = self.extract_log_messages(data)

        # 获取元数据信息
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        tag_infos = data.get("tag_infos", []) if isinstance(data, dict) else []

        # 返回结构化的日志详细信息
        return {
            "logid": logid,  # 日志 ID
            "messages": messages,  # 提取的日志消息
            "meta": meta,  # 元数据
            "tag_infos": tag_infos,  # 标签信息
            "total_items": len(messages),  # 消息总数
            "scan_time_range": meta.get("scan_time_range", []),  # 扫描时间范围
            "level_list": meta.get("level_list", []),  # 日志级别列表
            "timestamp": result.get("timestamp", "Unknown"),  # 查询时间戳
            "region": result.get("region", "unknown"),  # 区域信息
            "region_display_name": result.get("region_display_name", "未知区域")  # 区域显示名称
        }

    def format_log_response(self, log_details: Dict[str, Any]) -> str:
        """
        格式化日志详情为可读响应

        将详细的日志信息格式化为用户友好的字符串响应，包含区域信息和消息详情。

        参数:
            log_details: 详细的日志信息

        返回:
            格式化的字符串响应
        """
        # 提取日志详情信息
        messages = log_details.get("messages", [])
        total_items = log_details.get("total_items", 0)
        logid = log_details.get("logid", "Unknown")
        scan_time_range = log_details.get("scan_time_range", [])
        region = log_details.get("region", "unknown")
        region_display_name = log_details.get("region_display_name", "未知区域")

        # 构建响应字符串
        response = f"""
📋 **日志查询结果**
🔍 **日志 ID**: {logid}
🌍 **查询区域**: {region_display_name} ({region})
📊 **消息总数**: {total_items}
"""

        # 添加扫描时间范围信息
        if scan_time_range:
            response += "⏰ **扫描时间范围**:\n"
            for i, time_range in enumerate(scan_time_range, 1):
                # 格式化时间戳
                start_time = datetime.fromtimestamp(time_range.get("start", 0)).strftime("%Y-%m-%d %H:%M:%S") if time_range.get("start") else "未知"
                end_time = datetime.fromtimestamp(time_range.get("end", 0)).strftime("%Y-%m-%d %H:%M:%S") if time_range.get("end") else "未知"
                response += f"  范围 {i}: {start_time} 到 {end_time}\n"

        # 添加日志消息详情
        if messages:
            response += "\n📝 **日志消息详情**:\n"
            for i, message in enumerate(messages, 1):
                # 提取分组信息
                group = message.get("group", {})
                psm = group.get("psm", "未知")
                pod_name = group.get("pod_name", "未知")
                ipv4 = group.get("ipv4", "未知")
                env = group.get("env", "未知")
                vregion = group.get("vregion", "未知")
                idc = group.get("idc", "未知")

                response += f"\n--- 消息 {i} ---\n"
                response += f"  🏷️ **PSM**: {psm}\n"
                response += f"  🐳 **Pod**: {pod_name}\n"
                response += f"  🌐 **IP 地址**: {ipv4}\n"
                response += f"  🌍 **虚拟区域**: {vregion}\n"
                response += f"  🏢 **IDC**: {idc}\n"
                response += f"  🔧 **环境**: {env}\n"

                # 添加消息内容
                values = message.get("values", [])
                for value in values:
                    if value.get("key") == "_msg":
                        response += f"  💬 **消息内容**: {value.get('value', '无消息内容')}\n"
                        if value.get("highlight"):
                            response += "  ✨ **高亮显示**: 是\n"
        else:
            response += "\n❌ **未找到日志消息**\n"

        # 添加查询时间戳
        response += f"\n⏰ **查询时间**: {log_details.get('timestamp', '未知')}"

        return response.strip()

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