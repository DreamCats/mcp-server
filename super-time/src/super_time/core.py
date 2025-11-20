"""
SuperTime 核心功能模块
包含所有时间处理的核心逻辑
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, AsyncIterator
from zoneinfo import ZoneInfo


async def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间的格式化字符串

    Args:
        format_str: 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

    Returns:
        格式化的时间字符串
    """
    return datetime.now().strftime(format_str)


async def get_current_timestamp() -> int:
    """
    获取当前时间戳（秒级）

    Returns:
        当前时间戳（秒）
    """
    return int(time.time())


async def get_timestamp_range(
    start_time: str,
    end_time: str,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> Dict[str, int]:
    """
    获取指定时间范围内的时间戳

    Args:
        start_time: 开始时间字符串
        end_time: 结束时间字符串
        format_str: 时间格式字符串

    Returns:
        包含开始和结束时间戳的字典
    """
    start_dt = datetime.strptime(start_time, format_str)
    end_dt = datetime.strptime(end_time, format_str)

    return {
        "start_timestamp": int(start_dt.timestamp()),
        "end_timestamp": int(end_dt.timestamp())
    }


async def get_time_range(
    start_time: str,
    end_time: str,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    interval_seconds: int = 60
) -> AsyncIterator[str]:
    """
    获取指定时间范围内的时间列表（流式返回）

    Args:
        start_time: 开始时间字符串
        end_time: 结束时间字符串
        format_str: 时间格式字符串
        interval_seconds: 时间间隔（秒），默认为60秒

    Yields:
        格式化的时间字符串
    """
    start_dt = datetime.strptime(start_time, format_str)
    end_dt = datetime.strptime(end_time, format_str)

    current_dt = start_dt
    while current_dt <= end_dt:
        yield current_dt.strftime(format_str)
        current_dt += timedelta(seconds=interval_seconds)
        await asyncio.sleep(0.001)  # 小延迟避免阻塞


async def get_timezone_time(
    timezone: str = "Asia/Shanghai",
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    获取指定时区的时间

    Args:
        timezone: 时区名称，如 "Asia/Shanghai", "America/New_York"
        format_str: 时间格式字符串

    Returns:
        指定时区的格式化时间字符串
    """
    try:
        tz = ZoneInfo(timezone)
        return datetime.now(tz).strftime(format_str)
    except Exception as e:
        return f"错误：无效的时区 '{timezone}' - {str(e)}"


async def get_timezone_timestamp(timezone: str = "Asia/Shanghai") -> int:
    """
    获取指定时区的时间戳

    Args:
        timezone: 时区名称

    Returns:
        指定时区的当前时间戳（秒）
    """
    try:
        tz = ZoneInfo(timezone)
        return int(datetime.now(tz).timestamp())
    except Exception as e:
        return f"错误：无效的时区 '{timezone}' - {str(e)}"


async def get_recent_time(
    minutes: int = 10,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    获取最近N分钟前的时间

    Args:
        minutes: 分钟数，默认为10分钟
        format_str: 时间格式字符串

    Returns:
        最近N分钟前的时间字符串
    """
    recent_dt = datetime.now() - timedelta(minutes=minutes)
    return recent_dt.strftime(format_str)


async def get_recent_timestamp(minutes: int = 10) -> int:
    """
    获取最近N分钟前的时间戳

    Args:
        minutes: 分钟数，默认为10分钟

    Returns:
        最近N分钟前的时间戳（秒）
    """
    recent_dt = datetime.now() - timedelta(minutes=minutes)
    return int(recent_dt.timestamp())


async def get_time_info(
    timezone: str = "Asia/Shanghai",
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> Dict[str, Any]:
    """
    获取完整的时间信息（包含多个格式）

    Args:
        timezone: 时区名称
        format_str: 时间格式字符串

    Returns:
        包含多种时间格式的信息字典
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)

        return {
            "timezone": timezone,
            "local_time": now.strftime(format_str),
            "iso_format": now.isoformat(),
            "timestamp": int(now.timestamp()),
            "timestamp_ms": int(now.timestamp() * 1000),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
            "weekday_cn": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
        }
    except Exception as e:
        return {"error": f"无效的时区 '{timezone}' - {str(e)}"}