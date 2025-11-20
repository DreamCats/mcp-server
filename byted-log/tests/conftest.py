"""
测试配置和工具函数
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any


def create_mock_context(headers: Dict[str, str] = None) -> Mock:
    """创建模拟的MCP上下文对象"""
    ctx = Mock()
    ctx.session_id = "test-session-123"
    ctx.get_http_headers = Mock(return_value=headers or {})
    ctx.set_state = Mock()
    ctx.get_state = Mock(return_value=None)
    return ctx


def create_test_headers(cookie_value: str = "1865f510d37eb4cf2447d210cbf17686", region: str = "us") -> Dict[str, str]:
    """创建测试用的headers"""
    return {
        "cookie": cookie_value,
        f"COOKIE_{region.upper()}": cookie_value
    }


class AsyncContextManagerMock:
    """异步上下文管理器模拟类"""
    def __init__(self, return_value=None):
        self.return_value = return_value
        self.enter_mock = AsyncMock(return_value=self.return_value)
        self.exit_mock = AsyncMock(return_value=None)

    async def __aenter__(self):
        return await self.enter_mock()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.exit_mock(exc_type, exc_val, exc_tb)


@pytest.fixture
def mock_jwt_manager():
    """JWT管理器模拟"""
    manager = AsyncMock()
    manager.get_jwt_token = AsyncMock(return_value="test-jwt-token")
    manager.close = AsyncMock()
    return manager


@pytest.fixture
def mock_log_query():
    """日志查询器模拟"""
    query = AsyncMock()
    query.query_logs_by_logid = AsyncMock(return_value={
        "status": "success",
        "total": 1,
        "logs": [{
            "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
            "message": "Test log message",
            "timestamp": "2024-01-01T12:00:00Z"
        }]
    })
    query.format_log_response = Mock(return_value="格式化后的日志结果")
    return query