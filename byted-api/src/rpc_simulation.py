"""
字节跳动 MCP 服务器 i18n RPC 请求模拟模块

本模块处理 TikTok ROW 环境中的 RPC 请求模拟，使用已发现的服务实例地址
进行 RPC 调用测试。支持通过 JWT 认证发送 RPC 请求并获取响应数据。
"""

import json
from typing import Dict, Optional, Any
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class RPCSimulator:
    """
    TikTok ROW RPC 请求模拟器

    提供基于 JWT 认证的 RPC 请求模拟功能，支持向已发现的服务实例
    发送 RPC 调用并获取响应数据，用于测试和调试服务接口。
    """

    def __init__(self, jwt_manager):
        """
        初始化 RPC 模拟器

        参数:
            jwt_manager: JWTAuthManager 实例，用于处理 JWT 认证
        """

    def __init__(self, jwt_manager):
        """
        初始化 RPC 模拟器

        参数:
            jwt_manager: JWTAuthManager 实例，用于处理 JWT 认证
        """
        self.jwt_manager = jwt_manager  # JWT 认证管理器

        # TikTok ROW RPC 请求模拟 API 端点
        self.rpc_url = "https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/rpc_request"

        # 配置 HTTP 客户端
        # 设置较长的超时时间（60秒）以适应 RPC 请求的响应时间
        self.client = httpx.AsyncClient(
            timeout=60.0,  # RPC 请求需要更长的超时时间
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/json",  # RPC 请求使用 JSON 格式
            }
        )

    async def simulate_rpc_request(self, psm: str, address: str, func_name: str,
                                 req_body: str, zone: str, idc: str,
                                 cluster: str = "default", env: str = "prod",
                                 request_timeout: int = 60000, idl_source: int = 1,
                                 idl_version: str = "master") -> Dict[str, Any]:
        """
        向 i18n 服务发送 RPC 请求模拟（使用已发现的实例地址）

        通过指定的实例地址发送 RPC 调用请求，模拟真实的 RPC 调用过程。
        支持自定义请求参数、超时设置和 IDL 配置。

        参数:
            psm: PSM 标识符（必需，如 "oec.affiliate.monitor"）
            address: 目标实例地址，格式为 [ip]:port（必需）
            func_name: 要调用的 RPC 方法名称（必需，如 "SearchLiveEvent"）
            req_body: JSON 字符串格式的请求体（必需）
            zone: 地理区域标识符（必需，如 "MVAALI", "SGALI"）
            idc: 数据中心标识符（必需，如 "maliva", "my", "sg1"）
            cluster: 集群名称（可选，默认为 "default"）
            env: 环境类型（可选，默认为 "prod"）
            request_timeout: 请求超时时间，单位为毫秒（可选，默认为 60000）
            idl_source: IDL 源标识（可选，默认为 1）
            idl_version: IDL 版本（可选，默认为 "master"）

        返回:
            RPC 响应字典，包含以下字段：
            - psm: PSM 名称
            - address: 目标实例地址
            - func_name: 调用的函数名称
            - zone/idc/cluster/env: 环境参数
            - request_data: 请求数据
            - response_data: 原始响应数据
            - performance: 性能指标（延迟、协议等）
            - response_body: 响应体内容（如可用）
            - business_status: 业务状态信息
            - debug_info: 调试信息（如可用）
            - timestamp: 请求时间戳

        异常:
            RuntimeError: 当 RPC 请求模拟失败时抛出，包含具体的错误信息

        示例:
            >>> result = await simulator.simulate_rpc_request(
            ...     psm="oec.affiliate.monitor",
            ...     address="[fdbd:dc61:2:151::195]:11503",
            ...     func_name="SearchLiveEvent",
            ...     req_body='{"room_id": "1730849136927543871", "author_id": "7280819145410593838"}',
            ...     zone="MVAALI",
            ...     idc="maliva"
            ... )
        """
        logger.info("Simulating RPC request",
                   psm=psm, address=address, func_name=func_name,
                   zone=zone, idc=idc, cluster=cluster, env=env)

        # 获取 JWT 认证令牌
        jwt_token = await self.jwt_manager.get_jwt_token()

        # 准备 RPC 请求体
        request_body = {
            "psm": psm,                           # PSM 标识符
            "func_name": func_name,               # RPC 方法名称
            "req_body": req_body,                 # 请求体内容
            "idl_source": idl_source,              # IDL 源标识
            "idl_version": idl_version,           # IDL 版本
            "zone": zone,                         # 区域信息
            "idc": idc,                           # IDC 信息
            "cluster": cluster,                   # 集群信息
            "env": env,                           # 环境信息
            "address": address,                   # 目标实例地址
            "rpc_context": [],                    # RPC 上下文（空列表）
            "request_timeout": request_timeout,   # 请求超时时间
            "connect_timeout": request_timeout,   # 连接超时时间（与请求超时相同）
            "online": True,                       # 在线模式
            "source": 1,                          # 源标识
            "base": {}                            # 基础配置（空字典）
        }

        headers = {"x-jwt-token": jwt_token}  # JWT 认证头

        try:
            logger.debug("Sending RPC request",
                        url=self.rpc_url,
                        headers=headers,
                        request_body=request_body)

            # 发送 HTTP POST 请求到 RPC 模拟 API
            response = await self.client.post(self.rpc_url, headers=headers, json=request_body)
            response.raise_for_status()  # 检查 HTTP 状态码

            # 解析 JSON 响应数据
            data = response.json()

            # 记录响应详情用于调试
            logger.debug("RPC simulation response",
                        status_code=response.status_code,
                        response_headers=dict(response.headers),
                        response_data=data)

            # 格式化响应结果
            result = {
                "psm": psm,                                    # PSM 名称
                "address": address,                            # 目标实例地址
                "func_name": func_name,                        # 调用的函数名称
                "zone": zone,                                  # 区域信息
                "idc": idc,                                    # IDC 信息
                "cluster": cluster,                            # 集群信息
                "env": env,                                    # 环境信息
                "request_data": request_body,                  # 请求数据
                "response_data": data,                         # 原始响应数据
                "timestamp": datetime.now().isoformat()      # 请求时间戳
            }

            # 提取关键指标和响应内容
            if isinstance(data, dict) and "data" in data:
                response_data = data.get("data", {})

                # 提取性能指标
                if isinstance(response_data, dict):
                    result["performance"] = {
                        "request_latency": response_data.get("req_latency"),    # 请求延迟
                        "request_at": response_data.get("request_at"),          # 请求时间
                        "finish_at": response_data.get("finish_at"),          # 完成时间
                        "protocol": response_data.get("protocol")               # 协议类型
                    }

                    # 提取响应体内容（如果可用）
                    resp_body = response_data.get("resp_body")
                    if resp_body:
                        try:
                            # 尝试解析为 JSON 以获得更好的格式化
                            parsed_resp = json.loads(resp_body)
                            result["response_body"] = parsed_resp
                        except json.JSONDecodeError:
                            # 如果不是有效的 JSON，保持为字符串
                            result["response_body"] = resp_body

                    # 提取调试信息
                    debug_info = response_data.get("debug_info", {})
                    if debug_info:
                        result["debug_info"] = debug_info

                    # 提取业务状态信息
                    result["business_status"] = {
                        "biz_status_code": response_data.get("biz_status_code"),  # 业务状态码
                        "error_message": response_data.get("error"),              # 错误消息
                        "help_message": response_data.get("help_message")         # 帮助消息
                    }

            logger.info("RPC simulation completed",
                       psm=psm,
                       func_name=func_name,
                       status_code=response.status_code,
                       has_response_body="response_body" in result)

            return result

        except httpx.TimeoutException:
            # 请求超时异常处理
            logger.error("RPC simulation timeout", psm=psm, address=address, timeout=request_timeout)
            raise RuntimeError(f"Timeout while simulating RPC request to {address} (timeout: {request_timeout}ms)")

        except httpx.HTTPError as e:
            # HTTP 错误异常处理
            logger.error("RPC simulation HTTP error",
                        psm=psm,
                        address=address,
                        error=str(e),
                        error_type=type(e).__name__)
            raise RuntimeError(f"HTTP error while simulating RPC request to {address}: {e}")

        except json.JSONDecodeError as e:
            # JSON 解析错误异常处理
            logger.error("RPC simulation JSON error",
                        psm=psm,
                        address=address,
                        error=str(e))
            raise RuntimeError(f"JSON error while processing RPC request/response: {e}")

        except Exception as e:
            # 其他未预期的异常处理
            logger.error("RPC simulation unexpected error",
                        psm=psm,
                        address=address,
                        error=str(e),
                        error_type=type(e).__name__)
            raise RuntimeError(f"Unexpected error while simulating RPC request to {address}: {e}")

    async def simulate_rpc_with_discovery(self, psm: str, func_name: str, req_body: str,
                                        zone: str, idc: str, cluster: str = "default",
                                        **kwargs) -> Dict[str, Any]:
        """
        便捷方法：结合实例发现与 RPC 模拟

        自动发现指定 PSM 的实例地址，然后使用发现的第一个实例进行 RPC 调用模拟。
        简化了手动指定实例地址的流程。

        参数:
            psm: PSM 标识符
            func_name: RPC 方法名称
            req_body: JSON 字符串格式的请求体
            zone: 地理区域标识符
            idc: 数据中心标识符
            cluster: 集群名称（可选，默认为 "default"）
            **kwargs: RPC 模拟的额外参数

        返回:
            组合结果字典，包含以下字段：
            - discovery: 实例发现结果（找到的实例数量、使用的实例、所有实例）
            - rpc_simulation: RPC 模拟结果
            - timestamp: 操作时间戳

        注意:
            此方法需要 instance_discovery 模块可用，会自动导入并使用
        """
        try:
            # 延迟导入以避免循环依赖
            from instance_discovery import InstanceDiscovery

            # 创建实例发现器实例
            instance_discovery = InstanceDiscovery(self.jwt_manager)

            # 发现实例地址
            logger.info("Auto-discovering instances for RPC simulation", psm=psm, zone=zone, idc=idc)
            instances_result = await instance_discovery.get_instance_details(psm, zone, idc, cluster)

            # 获取实例列表
            instances = instances_result.get("instances", [])
            if not instances:
                raise RuntimeError(f"No instances found for PSM: {psm} in zone: {zone}, idc: {idc}")

            # 使用第一个可用的实例
            first_instance = instances[0]
            if isinstance(first_instance, str):
                # 字符串格式：直接作为地址
                address = first_instance
            else:
                # 字典格式：转换为字符串
                address = str(first_instance)

            logger.info("Using discovered instance for RPC simulation", address=address)

            # 执行 RPC 请求模拟
            rpc_result = await self.simulate_rpc_request(
                psm=psm,
                address=address,
                func_name=func_name,
                req_body=req_body,
                zone=zone,
                idc=idc,
                cluster=cluster,
                **kwargs
            )

            # 组合发现结果和 RPC 模拟结果
            return {
                "discovery": {
                    "instances_found": len(instances),    # 发现的实例数量
                    "used_instance": address,              # 使用的实例地址
                    "all_instances": instances             # 所有发现的实例
                },
                "rpc_simulation": rpc_result,              # RPC 模拟结果
                "timestamp": datetime.now().isoformat()   # 操作时间戳
            }

        except ImportError:
            # 导入失败异常处理
            logger.error("InstanceDiscovery module not available for auto-discovery")
            raise RuntimeError("InstanceDiscovery module required for auto-discovery feature")

        except Exception as e:
            # 其他异常处理
            logger.error("Auto-discovery RPC simulation failed", error=str(e))
            raise RuntimeError(f"Auto-discovery RPC simulation failed: {e}")

    def format_rpc_response(self, result: Dict[str, Any]) -> str:
        """
        格式化 RPC 模拟结果以供用户友好显示

        将 RPC 模拟结果转换为易读的格式化字符串，包含关键信息如 PSM、
        函数名称、地址、性能指标、响应内容等。

        参数:
            result: RPC 模拟结果字典，包含模拟的完整信息

        返回:
            格式化的字符串，包含所有关键信息的易读展示
        """
        # 获取 RPC 数据，支持两种格式（直接结果或包含 rpc_simulation 的包装格式）
        rpc_data = result.get("rpc_simulation", result)  # 处理两种格式

        # 构建基础响应信息
        response = f"""
🚀 **RPC 模拟结果**
🔧 **PSM**: {rpc_data.get("psm", "未知")}
🎯 **函数**: {rpc_data.get("func_name", "未知")}
🌐 **地址**: {rpc_data.get("address", "未知")}
🌍 **区域**: {rpc_data.get("zone", "未知")}
🏢 **IDC**: {rpc_data.get("idc", "未知")}
"""

        # 添加性能指标（如果可用）
        performance = rpc_data.get("performance", {})
        if performance:
            response += f"\n⚡ **性能指标**:\n"
            if performance.get("request_latency"):
                response += f"  延迟: {performance['request_latency']}\n"
            if performance.get("protocol"):
                response += f"  协议: {performance['protocol']}\n"

        # 添加业务状态（如果可用）
        business_status = rpc_data.get("business_status", {})
        if business_status:
            response += f"\n📊 **业务状态**:\n"
            if business_status.get("biz_status_code") is not None:
                response += f"  状态码: {business_status['biz_status_code']}\n"
            if business_status.get("error_message"):
                response += f"  错误: {business_status['error_message']}\n"

        # 添加响应体（如果可用）
        response_body = rpc_data.get("response_body")
        if response_body:
            response += f"\n📄 **响应体**:\n"
            if isinstance(response_body, dict):
                # 格式化 JSON 响应
                response += json.dumps(response_body, indent=2, ensure_ascii=False)
            else:
                response += str(response_body)

        # 添加调试信息（如果可用）
        debug_info = rpc_data.get("debug_info")
        if debug_info:
            response += f"\n\n🔍 **调试信息**:\n"
            response += json.dumps(debug_info, indent=2, ensure_ascii=False)

        response += f"\n\n⏰ **时间戳**: {rpc_data.get('timestamp', '未知')}"

        return response.strip()

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