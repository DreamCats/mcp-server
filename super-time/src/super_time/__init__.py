"""
基于 fastmcp 的灵活时间获取服务
支持 streamable HTTP 协议
"""

from fastmcp import FastMCP
from .core import (
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

# 创建 FastMCP 实例
mcp = FastMCP(
    name="SuperTime",
    version="0.1.0"
)


@mcp.tool()
async def current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间的格式化字符串"""
    return await get_current_time(format_str)


@mcp.tool()
async def current_timestamp() -> int:
    """获取当前时间戳（秒级）"""
    return await get_current_timestamp()


@mcp.tool()
async def timestamp_range(
    start_time: str,
    end_time: str,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> dict:
    """获取指定时间范围内的时间戳"""
    return await get_timestamp_range(start_time, end_time, format_str)


@mcp.tool()
async def time_range(
    start_time: str,
    end_time: str,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    interval_seconds: int = 60
) -> str:
    """获取指定时间范围内的时间列表（流式返回）"""
    results = []
    async for time_str in get_time_range(start_time, end_time, format_str, interval_seconds):
        results.append(time_str)
    return "\n".join(results)


@mcp.tool()
async def timezone_time(
    timezone: str = "Asia/Shanghai",
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """获取指定时区的时间"""
    return await get_timezone_time(timezone, format_str)


@mcp.tool()
async def timezone_timestamp(timezone: str = "Asia/Shanghai") -> int:
    """获取指定时区的时间戳"""
    return await get_timezone_timestamp(timezone)


@mcp.tool()
async def recent_time(
    minutes: int = 10,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """获取最近N分钟前的时间"""
    return await get_recent_time(minutes, format_str)


@mcp.tool()
async def recent_timestamp(minutes: int = 10) -> int:
    """获取最近N分钟前的时间戳"""
    return await get_recent_timestamp(minutes)


@mcp.tool()
async def time_info(
    timezone: str = "Asia/Shanghai",
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> dict:
    """获取完整的时间信息（包含多个格式）"""
    return await get_time_info(timezone, format_str)


if __name__ == "__main__":
    # 运行MCP服务
    mcp.run()