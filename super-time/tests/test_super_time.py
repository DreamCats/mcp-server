"""
SuperTime MCP 服务测试用例
"""

import asyncio
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from super_time.core import (
    get_current_time,
    get_current_timestamp,
    get_timestamp_range,
    get_time_range,
    get_timezone_time,
    get_timezone_timestamp,
    get_recent_time,
    get_recent_timestamp,
    get_time_info,
)


class TestSuperTime:
    """SuperTime 功能测试类"""

    @pytest.mark.asyncio
    async def test_get_current_time(self):
        """测试获取当前时间"""
        result = await get_current_time()
        assert isinstance(result, str)
        # 验证时间格式
        try:
            datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pytest.fail("时间格式不正确")

    @pytest.mark.asyncio
    async def test_get_current_timestamp(self):
        """测试获取当前时间戳"""
        result = await get_current_timestamp()
        assert isinstance(result, int)
        # 验证时间戳在合理范围内（过去1小时到未来1分钟）
        now = int(datetime.now().timestamp())
        assert now - 3600 <= result <= now + 60

    @pytest.mark.asyncio
    async def test_get_timestamp_range(self):
        """测试获取时间戳范围"""
        start_time = "2023-01-01 00:00:00"
        end_time = "2023-01-01 01:00:00"

        result = await get_timestamp_range(start_time, end_time)

        assert isinstance(result, dict)
        assert "start_timestamp" in result
        assert "end_timestamp" in result
        assert isinstance(result["start_timestamp"], int)
        assert isinstance(result["end_timestamp"], int)

        # 验证时间戳差值为1小时（3600秒）
        assert result["end_timestamp"] - result["start_timestamp"] == 3600

    @pytest.mark.asyncio
    async def test_get_time_range(self):
        """测试获取时间范围列表"""
        start_time = "2023-01-01 00:00:00"
        end_time = "2023-01-01 00:05:00"

        results = []
        async for time_str in get_time_range(start_time, end_time, interval_seconds=60):
            results.append(time_str)

        # 应该返回6个时间点（包含开始和结束）
        assert len(results) == 6
        assert results[0] == "2023-01-01 00:00:00"
        assert results[-1] == "2023-01-01 00:05:00"

    @pytest.mark.asyncio
    async def test_get_timezone_time(self):
        """测试获取指定时区时间"""
        # 测试东八区
        result = await get_timezone_time("Asia/Shanghai")
        assert isinstance(result, str)

        # 测试UTC
        result_utc = await get_timezone_time("UTC")
        assert isinstance(result_utc, str)

        # 测试无效时区
        result_invalid = await get_timezone_time("Invalid/Timezone")
        assert "错误" in result_invalid

    @pytest.mark.asyncio
    async def test_get_timezone_timestamp(self):
        """测试获取指定时区时间戳"""
        result = await get_timezone_timestamp("Asia/Shanghai")
        assert isinstance(result, int)

        # 测试无效时区
        result_invalid = await get_timezone_timestamp("Invalid/Timezone")
        assert "错误" in result_invalid

    @pytest.mark.asyncio
    async def test_get_recent_time(self):
        """测试获取最近时间"""
        result = await get_recent_time(minutes=30)
        assert isinstance(result, str)

        # 验证时间格式
        try:
            datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pytest.fail("时间格式不正确")

    @pytest.mark.asyncio
    async def test_get_recent_timestamp(self):
        """测试获取最近时间戳"""
        result = await get_recent_timestamp(minutes=30)
        assert isinstance(result, int)

        # 验证时间戳在合理范围内
        now = int(datetime.now().timestamp())
        assert now - 1800 <= result <= now  # 30分钟前到现在

    @pytest.mark.asyncio
    async def test_get_time_info(self):
        """测试获取完整时间信息"""
        result = await get_time_info("Asia/Shanghai")

        assert isinstance(result, dict)
        assert "timezone" in result
        assert "local_time" in result
        assert "iso_format" in result
        assert "timestamp" in result
        assert "date" in result
        assert "time" in result
        assert "weekday_cn" in result

        # 验证时区
        assert result["timezone"] == "Asia/Shanghai"

        # 验证时间戳
        assert isinstance(result["timestamp"], int)

    @pytest.mark.asyncio
    async def test_custom_time_format(self):
        """测试自定义时间格式"""
        custom_format = "%Y年%m月%d日 %H时%M分%S秒"
        result = await get_current_time(custom_format)

        # 验证包含中文字符
        assert "年" in result
        assert "月" in result
        assert "日" in result

    @pytest.mark.asyncio
    async def test_streamable_time_range(self):
        """测试流式时间范围返回"""
        start_time = "2023-01-01 00:00:00"
        end_time = "2023-01-01 00:02:00"

        count = 0
        async for time_str in get_time_range(start_time, end_time, interval_seconds=30):
            count += 1
            assert isinstance(time_str, str)

        # 应该返回5个时间点（0, 30, 60, 90, 120秒）
        assert count == 5


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])