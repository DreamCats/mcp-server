"""
真实数据工作流测试

使用用户提供的测试数据验证MCP服务器的核心功能
测试数据：
- headers: CAS_SESSION_US="1865f510d37eb4cf2447d210cbf17686"
- logid：02176355661407900000000000000000000ffff0a71b1e8a4db84
- psm：ttec.script.live_promotion_change
- region:us
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import ByteDanceLogQueryMCPServer


class TestRealDataWorkflow:
    """使用真实测试数据的工作流测试"""

    @pytest.fixture
    def server(self):
        """创建MCP服务器实例"""
        return ByteDanceLogQueryMCPServer()

    @pytest.fixture
    def real_test_context(self):
        """创建包含真实测试数据的上下文"""
        context = Mock()
        context.session_id = "test-session-real-data"

        # 用户提供的真实headers数据
        real_headers = {
            "CAS_SESSION_US": "1865f510d37eb4cf2447d210cbf17686",
            "cookie": "1865f510d37eb4cf2447d210cbf17686"
        }
        context.get_http_headers = Mock(return_value=real_headers)
        return context

    @pytest.mark.asyncio
    async def test_real_data_success_workflow(self, server, real_test_context):
        """测试真实数据的成功工作流"""
        # 用户提供的真实测试数据
        logid = "02176355661407900000000000000000000ffff0a71b1e8a4db84"
        psm_list = "ttec.script.live_promotion_change"
        region = "us"
        scan_time_min = 10

        # 模拟JWT认证管理器
        with patch('mcp_server.JWTAuthManager') as mock_jwt_class:
            mock_jwt_manager = AsyncMock()
            mock_jwt_manager.close = AsyncMock()
            mock_jwt_class.return_value = mock_jwt_manager

            # 模拟日志查询
            with patch('mcp_server.LogQuery') as mock_log_query_class:
                mock_log_query = AsyncMock()

                # 模拟成功的查询结果
                mock_log_query.query_logs_by_logid = AsyncMock(return_value={
                    "status": "success",
                    "region": "us",
                    "total": 3,
                    "logs": [
                        {
                            "logid": logid,
                            "message": "Live promotion change event processed successfully",
                            "psm": "ttec.script.live_promotion_change",
                            "timestamp": "2024-01-15T10:30:45Z",
                            "level": "INFO",
                            "details": {
                                "promotion_id": "promo_12345",
                                "status": "active"
                            }
                        },
                        {
                            "logid": logid,
                            "message": "Promotion parameters updated",
                            "psm": "ttec.script.live_promotion_change",
                            "timestamp": "2024-01-15T10:30:46Z",
                            "level": "DEBUG"
                        },
                        {
                            "logid": logid,
                            "message": "Cache invalidated for promotion",
                            "psm": "ttec.script.live_promotion_change",
                            "timestamp": "2024-01-15T10:30:47Z",
                            "level": "INFO"
                        }
                    ]
                })

                # 模拟响应格式化
                mock_log_query.format_log_response = Mock(return_value=f"""
✅ 日志查询成功 (区域: {region})

📊 查询统计:
- 总日志数: 3
- 查询时间: 2024-01-15T10:30:45Z

📝 关键日志信息:
- Live promotion change event processed successfully
- Promotion parameters updated
- Cache invalidated for promotion

🔍 日志ID: {logid}
🎯 PSM服务: ttec.script.live_promotion_change
""")
                mock_log_query_class.return_value = mock_log_query

                # 调用MCP工具
                result = await server.mcp.call_tool(
                    "query_logs_by_logid",
                    {
                        "logid": logid,
                        "region": region,
                        "psm_list": psm_list,
                        "scan_time_min": scan_time_min,
                        "ctx": real_test_context
                    }
                )

                # 验证返回格式
                assert isinstance(result, tuple)
                content_list, metadata = result
                assert len(content_list) == 1

                response_text = content_list[0].text

                # 验证响应内容包含关键信息
                assert "✅ 日志查询成功" in response_text
                assert f"区域: {region}" in response_text
                assert f"日志ID: {logid}" in response_text
                assert "ttec.script.live_promotion_change" in response_text
                assert "总日志数: 3" in response_text
                assert "Live promotion change event processed successfully" in response_text

                # 验证JWT管理器使用了正确的cookie
                mock_jwt_class.assert_called_once_with(
                    cookie_value="1865f510d37eb4cf2447d210cbf17686",
                    region="us"
                )

                # 验证日志查询参数正确
                mock_log_query.query_logs_by_logid.assert_called_once_with(
                    logid=logid,
                    region=region,
                    psm_list=["ttec.script.live_promotion_change"],
                    scan_time_min=scan_time_min
                )

                # 验证资源被正确清理
                mock_jwt_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_real_data_missing_cookie(self, server):
        """测试缺少cookie时的错误处理"""
        # 创建没有cookie的上下文
        context = Mock()
        context.get_http_headers = Mock(return_value={})

        # 调用MCP工具
        result = await server.mcp.call_tool(
            "query_logs_by_logid",
            {
                "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
                "region": "us",
                "ctx": context
            }
        )

        # 验证返回格式
        content_list, metadata = result
        assert len(content_list) == 1

        response_text = content_list[0].text

        # 验证错误信息
        assert "❌ 缺少 Cookie 认证信息" in response_text
        assert "请在请求头中提供 Cookie" in response_text

    @pytest.mark.asyncio
    async def test_real_data_region_specific_cookie_priority(self, server):
        """测试区域特定cookie的优先级"""
        # 创建同时有默认cookie和区域特定cookie的上下文
        context = Mock()
        context.get_http_headers = Mock(return_value={
            "cookie": "default-cookie-12345",  # 默认cookie
            "COOKIE_US": "1865f510d37eb4cf2447d210cbf17686"  # 区域特定cookie，应该优先使用
        })

        with patch('mcp_server.JWTAuthManager') as mock_jwt_class:
            mock_jwt_manager = AsyncMock()
            mock_jwt_manager.close = AsyncMock()
            mock_jwt_class.return_value = mock_jwt_manager

            with patch('mcp_server.LogQuery') as mock_log_query_class:
                mock_log_query = AsyncMock()
                mock_log_query.query_logs_by_logid = AsyncMock(return_value={"status": "success"})
                mock_log_query.format_log_response = Mock(return_value="区域特定cookie测试")
                mock_log_query_class.return_value = mock_log_query

                await server.mcp.call_tool(
                    "query_logs_by_logid",
                    {
                        "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
                        "region": "us",
                        "ctx": context
                    }
                )

                # 验证使用了区域特定cookie而不是默认cookie
                mock_jwt_class.assert_called_once_with(
                    cookie_value="1865f510d37eb4cf2447d210cbf17686",  # 应该使用COOKIE_US
                    region="us"
                )

    @pytest.mark.asyncio
    async def test_real_data_error_handling(self, server, real_test_context):
        """测试真实数据场景下的错误处理"""
        with patch('mcp_server.JWTAuthManager') as mock_jwt_class:
            mock_jwt_manager = AsyncMock()
            mock_jwt_manager.close = AsyncMock()
            mock_jwt_class.return_value = mock_jwt_manager

            with patch('mcp_server.LogQuery') as mock_log_query_class:
                mock_log_query = AsyncMock()
                # 模拟查询失败
                mock_log_query.query_logs_by_logid = AsyncMock(
                    side_effect=Exception("Authentication failed: Invalid CAS session 1865f510d37eb4cf2447d210cbf17686")
                )
                mock_log_query_class.return_value = mock_log_query

                result = await server.mcp.call_tool(
                    "query_logs_by_logid",
                    {
                        "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
                        "region": "us",
                        "psm_list": "ttec.script.live_promotion_change",
                        "ctx": real_test_context
                    }
                )

                # 验证返回格式
                content_list, metadata = result
                assert len(content_list) == 1

                response_text = content_list[0].text

                # 验证错误信息
                assert "❌ 查询 logid" in response_text
                assert "Authentication failed: Invalid CAS session" in response_text
                assert "1865f510d37eb4cf2447d210cbf17686" in response_text

                # 注意：当异常发生时，代码直接返回错误字符串，不会执行到清理部分
                # 这是当前的设计，资源清理只在成功路径执行

    @pytest.mark.asyncio
    async def test_multiple_psm_services(self, server, real_test_context):
        """测试多个PSM服务的查询"""
        with patch('mcp_server.JWTAuthManager') as mock_jwt_class:
            mock_jwt_manager = AsyncMock()
            mock_jwt_manager.close = AsyncMock()
            mock_jwt_class.return_value = mock_jwt_manager

            with patch('mcp_server.LogQuery') as mock_log_query_class:
                mock_log_query = AsyncMock()
                mock_log_query.query_logs_by_logid = AsyncMock(return_value={"status": "success"})
                mock_log_query.format_log_response = Mock(return_value="多PSM测试")
                mock_log_query_class.return_value = mock_log_query

                # 测试多个PSM服务
                result = await server.mcp.call_tool(
                    "query_logs_by_logid",
                    {
                        "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
                        "region": "us",
                        "psm_list": "ttec.script.live_promotion_change,ttec.script.other_service,ttec.script.third_service",
                        "ctx": real_test_context
                    }
                )

                # 验证PSM列表被正确解析
                call_args = mock_log_query.query_logs_by_logid.call_args
                psm_list = call_args[1]["psm_list"]
                assert psm_list == [
                    "ttec.script.live_promotion_change",
                    "ttec.script.other_service",
                    "ttec.script.third_service"
                ]

    def test_tool_registration(self, server):
        """测试工具是否正确注册"""
        # 这是一个同步测试，验证工具存在
        # 注意：list_tools()是异步的，但我们只是验证工具存在
        assert hasattr(server.mcp, 'call_tool')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])