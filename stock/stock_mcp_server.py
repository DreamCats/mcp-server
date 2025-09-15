"""股票数据 MCP 服务器

基于 FastMCP 框架的股票金融数据服务，为 AI 大模型提供中国股市数据查询能力。
使用 akshare 库作为数据源，通过 MCP 协议提供标准化的股票数据接口。

主要功能:
- 历史行情查询 (get_stock_history)
- 分时数据查询 (get_stock_intraday) 
- 近期历史行情 (get_recent_history)

作者: Stock MCP Team
版本: 1.0.0
"""

import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import akshare as ak
import httpx
import pandas as pd
import uvicorn

from mcp.server.fastmcp import FastMCP


# 初始化 FastMCP 服务器，用于股票数据工具
# json_response=False: 使用 SSE 流式响应而非 JSON
# stateless_http=False: 使用有状态模式，保持连接状态
mcp = FastMCP(name="stock", json_response=True, stateless_http=True)

# 服务常量配置
USER_AGENT = "stock-mcp-server/1.0"  # 用户代理标识
REQUEST_TIMEOUT = 30.0               # 请求超时时间（秒）
DEFAULT_PERIOD = "daily"             # 默认数据周期
DEFAULT_INTRADAY_PERIOD = "60"       # 默认分时数据间隔（分钟）
RECENT_DAYS = 20                      # 近期历史数据天数


def validate_stock_symbol(symbol: str) -> bool:
    """验证股票代码格式
    
    检查股票代码是否符合中国A股6位数字格式要求。
    
    Args:
        symbol (str): 待验证的股票代码
        
    Returns:
        bool: 代码格式有效返回 True，否则返回 False
        
    Example:
        >>> validate_stock_symbol("000001")
        True
        >>> validate_stock_symbol("12345")
        False
    """
    # 检查是否为空或长度不等于6
    if not symbol or len(symbol) != 6:
        return False
    
    # 检查是否全为数字
    if not symbol.isdigit():
        return False
        
    return True


def format_date_string(date_str: str) -> str:
    """格式化日期字符串
    
    将输入的日期字符串转换为 akshare 要求的 YYYYMMDD 格式。
    
    Args:
        date_str (str): 输入日期字符串，支持多种格式
        
    Returns:
        str: 格式化后的日期字符串 (YYYYMMDD)
        
    Raises:
        ValueError: 当日期格式无效时抛出异常
    """
    if not date_str:
        return ""
    
    # 移除常见的分隔符
    clean_date = date_str.replace("-", "").replace("/", "").replace(".", "")
    
    # 验证格式是否为8位数字
    if len(clean_date) == 8 and clean_date.isdigit():
        return clean_date
    
    raise ValueError(f"无效的日期格式: {date_str}，请使用 YYYYMMDD 格式")


def get_recent_date_range() -> tuple[str, str]:
    """获取近期日期范围
    
    计算从今天往前推 RECENT_DAYS 天的日期范围，用于近期历史数据查询。
    
    Returns:
        tuple[str, str]: (开始日期, 结束日期) 格式为 YYYYMMDD
        
    Example:
        >>> get_recent_date_range()  # 假设今天是 2024-12-13
        ('20241210', '20241213')
    """
    # 获取今天的日期
    today = datetime.now()
    
    # 计算开始日期（往前推 RECENT_DAYS 天）
    start_date = today - timedelta(days=RECENT_DAYS)
    
    # 格式化为 YYYYMMDD 字符串
    start_str = start_date.strftime("%Y%m%d")
    end_str = today.strftime("%Y%m%d")
    
    return start_str, end_str


async def safe_akshare_call(func_name: str, **kwargs) -> Optional[pd.DataFrame]:
    """安全调用 akshare 函数
    
    封装 akshare 函数调用，提供统一的错误处理和超时控制。
    
    Args:
        func_name (str): akshare 函数名称
        **kwargs: 传递给 akshare 函数的参数
        
    Returns:
        Optional[pd.DataFrame]: 成功时返回数据框，失败时返回 None
        
    Example:
        >>> data = await safe_akshare_call("stock_zh_a_hist", symbol="000001")
    """
    try:
        # 获取 akshare 函数
        ak_func = getattr(ak, func_name)
        
        # 在线程池中执行同步的 akshare 调用
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: ak_func(**kwargs))
        
        return result
        
    except AttributeError:
        # akshare 函数不存在
        print(f"错误: akshare 中不存在函数 {func_name}")
        return None
        
    except Exception as e:
        # 其他异常（网络错误、数据错误等）
        print(f"调用 {func_name} 失败: {str(e)}")
        return None


def format_dataframe_to_string(df: pd.DataFrame, title: str = "数据") -> str:
    """将 DataFrame 格式化为可读字符串
    
    将 pandas DataFrame 转换为格式化的字符串，便于 AI 模型理解和展示。
    
    Args:
        df (pd.DataFrame): 要格式化的数据框
        title (str, optional): 数据标题. Defaults to "数据".
        
    Returns:
        str: 格式化后的字符串
        
    Example:
        >>> df = pd.DataFrame({"日期": ["2024-12-13"], "收盘": [10.50]})
        >>> format_dataframe_to_string(df, "股票数据")
        "=== 股票数据 ===\\n日期: 2024-12-13, 收盘: 10.50\\n"
    """
    if df is None or df.empty:
        return f"=== {title} ===\n暂无数据\n"
    
    # 构建格式化字符串
    result = f"=== {title} ===\n"
    
    # 遍历每一行数据
    for _, row in df.iterrows():
        # 构建单行数据字符串
        row_data = []
        for col, value in row.items():
            # 格式化数值
            if pd.isna(value):
                formatted_value = "N/A"
            elif isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            row_data.append(f"{col}: {formatted_value}")
        
        # 添加到结果中
        result += ", ".join(row_data) + "\n"
    
    return result


@mcp.tool()
async def get_stock_history(
    symbol: str,
    period: str = DEFAULT_PERIOD,
    start_date: str = "",
    end_date: str = "",
    adjust: str = ""
) -> str:
    """获取股票历史行情数据

    通过 akshare 接口获取指定股票的历史交易数据，支持不同周期和复权方式。
    这是 MCP 工具函数，为 AI 模型提供股票历史数据查询能力。

    Args:
        symbol (str): 股票代码，6位数字格式，如 "000001" (平安银行)
        period (str, optional): 数据周期. Defaults to "daily".
            - "daily": 日线数据
            - "weekly": 周线数据
            - "monthly": 月线数据
        start_date (str, optional): 开始日期，格式 "YYYYMMDD". Defaults to "".
            如果为空，则获取所有可用历史数据
        end_date (str, optional): 结束日期，格式 "YYYYMMDD". Defaults to "".
            如果为空，则获取到最新日期
        adjust (str, optional): 复权方式. Defaults to "".
            - "": 不复权（原始价格）
            - "qfq": 前复权（除权除息后调整历史价格）
            - "hfq": 后复权（以最新价格为基准调整历史价格）

    Returns:
        str: 格式化的历史行情数据字符串，包含以下信息：
            - 日期、股票代码、开盘价、收盘价、最高价、最低价
            - 成交量（手）、成交额（元）、振幅（%）、涨跌幅（%）
            - 涨跌额（元）、换手率（%）

    Raises:
        无直接异常抛出，所有错误都转换为错误信息字符串返回

    Example:
        >>> await get_stock_history("000001", "daily", "20241201", "20241231")
        "=== 000001 历史行情数据 ===\\n日期: 2024-12-01, 开盘: 10.50, ..."

        >>> await get_stock_history("600519", "weekly")
        "=== 600519 历史行情数据 ===\\n日期: 2024-12-09, 开盘: 1650.00, ..."
    """
    # 第一步：验证股票代码格式
    if not validate_stock_symbol(symbol):
        return f"错误: 股票代码格式无效。请输入6位数字代码，如 '000001'，当前输入: '{symbol}'"

    # 第二步：验证数据周期参数
    valid_periods = ["daily", "weekly", "monthly"]
    if period not in valid_periods:
        return f"错误: 数据周期无效。支持的周期: {', '.join(valid_periods)}，当前输入: '{period}'"

    # 第三步：验证复权方式参数
    valid_adjusts = ["", "qfq", "hfq"]
    if adjust not in valid_adjusts:
        return f"错误: 复权方式无效。支持的方式: {', '.join(valid_adjusts)}，当前输入: '{adjust}'"

    # 第四步：格式化日期参数
    try:
        formatted_start = format_date_string(start_date) if start_date else ""
        formatted_end = format_date_string(end_date) if end_date else ""
    except ValueError as e:
        return f"错误: {str(e)}"

    # 第五步：构建 akshare 调用参数
    ak_params = {
        "symbol": symbol,
        "period": period,
        "adjust": adjust
    }

    # 添加日期参数（如果提供）
    if formatted_start:
        ak_params["start_date"] = formatted_start
    if formatted_end:
        ak_params["end_date"] = formatted_end

    # 第六步：调用 akshare 获取数据
    print(f"正在获取股票 {symbol} 的历史行情数据...")
    df = await safe_akshare_call("stock_zh_a_hist", **ak_params)

    # 第七步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取股票 {symbol} 的历史数据。请检查股票代码是否正确或稍后重试。"

    if df.empty:
        date_info = f"（{formatted_start} 到 {formatted_end}）" if formatted_start or formatted_end else ""
        return f"暂无数据: 股票 {symbol} 在指定时间范围内{date_info}没有交易数据。"

    # 第八步：格式化数据并返回
    title = f"{symbol} 历史行情数据（{period}）"
    if formatted_start or formatted_end:
        title += f" - {formatted_start or '开始'} 至 {formatted_end or '最新'}"

    result = format_dataframe_to_string(df, title)

    # 添加数据统计信息
    result += f"\n数据统计: 共 {len(df)} 条记录"
    if not df.empty:
        latest_date = df.iloc[-1]['日期'] if '日期' in df.columns else "未知"
        result += f"，最新日期: {latest_date}"

    return result


@mcp.tool()
async def get_stock_intraday(
    symbol: str,
    date: str = "",
    period: str = DEFAULT_INTRADAY_PERIOD,
    adjust: str = ""
) -> str:
    """获取股票分时数据

    通过 akshare 接口获取指定股票的分时交易数据，支持多种时间间隔。
    这是 MCP 工具函数，为 AI 模型提供股票分时数据查询能力。

    Args:
        symbol (str): 股票代码，6位数字格式，如 "000001" (平安银行)
        date (str, optional): 查询日期，格式 "YYYYMMDD". Defaults to "".
            如果为空，则获取最近可用的分时数据
        period (str, optional): 分时间隔. Defaults to "60".
            - "1": 1分钟（仅返回近5个交易日数据且不复权）
            - "5": 5分钟
            - "15": 15分钟
            - "30": 30分钟
            - "60": 60分钟（推荐，数据较稳定）
        adjust (str, optional): 复权方式. Defaults to "".
            - "": 不复权
            - "qfq": 前复权
            - "hfq": 后复权
            注意：1分钟数据不支持复权

    Returns:
        str: 格式化的分时数据字符串，包含以下信息：
            - 时间、开盘价、收盘价、最高价、最低价
            - 成交量（手）、成交额（元）、均价（元）

    Example:
        >>> await get_stock_intraday("000001", "20241213", "60")
        "=== 000001 分时数据 (60分钟) ===\\n时间: 09:30:00, 开盘: 10.50, ..."

        >>> await get_stock_intraday("600519", period="30")
        "=== 600519 分时数据 (30分钟) ===\\n时间: 09:30:00, 开盘: 1650.00, ..."
    """
    # 第一步：验证股票代码格式
    if not validate_stock_symbol(symbol):
        return f"错误: 股票代码格式无效。请输入6位数字代码，如 '000001'，当前输入: '{symbol}'"

    # 第二步：验证分时间隔参数
    valid_periods = ["1", "5", "15", "30", "60"]
    if period not in valid_periods:
        return f"错误: 分时间隔无效。支持的间隔: {', '.join(valid_periods)} 分钟，当前输入: '{period}'"

    # 第三步：验证复权方式参数
    valid_adjusts = ["", "qfq", "hfq"]
    if adjust not in valid_adjusts:
        return f"错误: 复权方式无效。支持的方式: {', '.join(valid_adjusts)}，当前输入: '{adjust}'"

    # 第四步：1分钟数据的特殊处理
    if period == "1" and adjust:
        return "警告: 1分钟数据不支持复权，已自动设置为不复权模式。"

    # 第五步：格式化日期参数
    try:
        if date:
            formatted_date = format_date_string(date)
        else:
            # 如果没有指定日期，使用今天的日期
            formatted_date = datetime.now().strftime("%Y%m%d")
    except ValueError as e:
        return f"错误: {str(e)}"

    # 第六步：构建时间范围（akshare 需要开始和结束时间）
    # 对于单日查询，设置为当天的交易时间范围
    start_datetime = f"{formatted_date} 09:30:00"  # 开盘时间
    end_datetime = f"{formatted_date} 15:00:00"    # 收盘时间

    # 第七步：构建 akshare 调用参数
    ak_params = {
        "symbol": symbol,
        "start_date": start_datetime,
        "end_date": end_datetime,
        "period": period,
        "adjust": adjust if period != "1" else ""  # 1分钟数据强制不复权
    }

    # 第八步：调用 akshare 获取分时数据
    print(f"正在获取股票 {symbol} 的分时数据（{period}分钟间隔）...")
    df = await safe_akshare_call("stock_zh_a_hist_min_em", **ak_params)

    # 第九步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取股票 {symbol} 的分时数据。请检查股票代码是否正确或稍后重试。"

    if df.empty:
        return f"暂无数据: 股票 {symbol} 在 {formatted_date} 没有分时交易数据。可能是非交易日或数据尚未更新。"

    # 第十步：格式化数据并返回
    title = f"{symbol} 分时数据 ({period}分钟间隔)"
    if date:
        title += f" - {formatted_date}"

    result = format_dataframe_to_string(df, title)

    # 添加数据统计信息
    result += f"\n数据统计: 共 {len(df)} 个时间点"
    if not df.empty and '时间' in df.columns:
        first_time = df.iloc[0]['时间']
        last_time = df.iloc[-1]['时间']
        result += f"，时间范围: {first_time} - {last_time}"

    # 添加特殊提示
    if period == "1":
        result += "\n注意: 1分钟数据仅包含近5个交易日且不支持复权。"

    return result


@mcp.tool()
async def get_recent_history(symbol: str, adjust: str = "") -> str:
    """获取股票近期历史行情

    快速获取指定股票近20天的历史交易数据，便于了解股票近期走势。
    这是 MCP 工具函数，为 AI 模型提供快速的近期行情查询能力。

    Args:
        symbol (str): 股票代码，6位数字格式，如 "000001" (平安银行)
        adjust (str, optional): 复权方式. Defaults to "".
            - "": 不复权（原始价格）
            - "qfq": 前复权（除权除息后调整历史价格）
            - "hfq": 后复权（以最新价格为基准调整历史价格）

    Returns:
        str: 格式化的近期历史行情数据字符串，包含：
            - 近3天的日线数据
            - 日期、开盘价、收盘价、最高价、最低价
            - 成交量、成交额、涨跌幅等关键指标
            - 简单的趋势分析

    Example:
        >>> await get_recent_history("000001")
        "=== 000001 近期历史行情 ===\\n日期: 2024-12-11, 收盘: 10.45, 涨跌幅: -1.23%\\n..."

        >>> await get_recent_history("600519", "qfq")
        "=== 600519 近期历史行情（前复权） ===\\n日期: 2024-12-11, 收盘: 1645.50, ..."
    """
    # 第一步：验证股票代码格式
    if not validate_stock_symbol(symbol):
        return f"错误: 股票代码格式无效。请输入6位数字代码，如 '000001'，当前输入: '{symbol}'"

    # 第二步：验证复权方式参数
    valid_adjusts = ["", "qfq", "hfq"]
    if adjust not in valid_adjusts:
        return f"错误: 复权方式无效。支持的方式: {', '.join(valid_adjusts)}，当前输入: '{adjust}'"

    # 第三步：获取近期日期范围
    start_date, end_date = get_recent_date_range()

    # 第四步：构建 akshare 调用参数
    ak_params = {
        "symbol": symbol,
        "period": "daily",  # 固定使用日线数据
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    }

    # 第五步：调用 akshare 获取数据
    print(f"正在获取股票 {symbol} 的近期历史行情（{start_date} - {end_date}）...")
    df = await safe_akshare_call("stock_zh_a_hist", **ak_params)

    # 第六步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取股票 {symbol} 的近期历史数据。请检查股票代码是否正确或稍后重试。"

    if df.empty:
        return f"暂无数据: 股票 {symbol} 在近{RECENT_DAYS}天内没有交易数据。可能是连续非交易日。"

    # 第七步：格式化数据标题
    title = f"{symbol} 近期历史行情（近{RECENT_DAYS}天）"
    if adjust:
        adjust_name = {"qfq": "前复权", "hfq": "后复权"}[adjust]
        title += f" - {adjust_name}"

    # 第八步：格式化基础数据
    result = format_dataframe_to_string(df, title)

    # 第九步：添加简单的趋势分析
    if len(df) >= 2 and '收盘' in df.columns and '涨跌幅' in df.columns:
        result += "\n=== 趋势分析 ===\n"

        # 获取最新和前一交易日的数据
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) >= 2 else None

        # 最新交易日信息
        latest_date = latest['日期'] if '日期' in df.columns else "最新"
        latest_close = latest['收盘']
        latest_change = latest['涨跌幅']

        result += f"最新交易日（{latest_date}）: 收盘价 {latest_close:.2f}元"

        # 涨跌幅分析
        if latest_change > 0:
            result += f"，上涨 {latest_change:.2f}% 📈\n"
        elif latest_change < 0:
            result += f"，下跌 {abs(latest_change):.2f}% 📉\n"
        else:
            result += f"，平盘 {latest_change:.2f}% ➡️\n"

        # 近期走势分析
        if previous is not None:
            prev_close = previous['收盘']
            price_change = latest_close - prev_close
            change_pct = (price_change / prev_close) * 100

            if change_pct > 0:
                trend = "上升趋势"
            elif change_pct < 0:
                trend = "下降趋势"
            else:
                trend = "横盘整理"

            result += f"较前一交易日: {trend}，价格变化 {price_change:+.2f}元 ({change_pct:+.2f}%)\n"

        # 成交量分析（如果有数据）
        if '成交量' in df.columns:
            avg_volume = df['成交量'].mean()
            latest_volume = latest['成交量']
            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio > 1.5:
                volume_desc = "放量"
            elif volume_ratio < 0.5:
                volume_desc = "缩量"
            else:
                volume_desc = "正常"

            result += f"成交量: {latest_volume}手，相对近期平均 {volume_desc} ({volume_ratio:.1f}倍)\n"

    # 第十步：添加数据统计信息
    result += f"\n数据统计: 共 {len(df)} 个交易日"
    if not df.empty:
        date_range = f"{df.iloc[0]['日期']} 至 {df.iloc[-1]['日期']}" if '日期' in df.columns else "未知范围"
        result += f"，时间范围: {date_range}"

    return result


@mcp.tool()
async def get_stock_info(symbol: str) -> str:
    """获取股票基本信息

    通过 akshare 的 stock_individual_info_em 接口获取指定股票的基本信息，
    包括股票代码、名称、总股本、流通股、市值、行业、上市时间等详细信息。
    这是 MCP 工具函数，为 AI 模型提供股票基本信息查询能力。

    Args:
        symbol (str): 股票代码，6位数字格式，如 "000001" (平安银行)

    Returns:
        str: 格式化的股票基本信息字符串，包含：
            - 股票代码、股票简称、最新价格
            - 总股本、流通股、总市值、流通市值
            - 所属行业、上市时间等基本信息

    Example:
        >>> await get_stock_info("000001")
        "=== 000001 股票基本信息 ===\\n股票简称: 平安银行, 最新价: 10.50元\\n..."

        >>> await get_stock_info("000002")
        "=== 000002 股票基本信息 ===\\n股票简称: 万科A, 最新价: 7.05元\\n..."
    """
    # 第一步：验证股票代码格式
    if not validate_stock_symbol(symbol):
        return f"错误: 股票代码格式无效。请输入6位数字代码，如 '000001'，当前输入: '{symbol}'"

    # 第二步：调用 akshare 获取个股信息
    print(f"正在获取股票 {symbol} 的基本信息...")
    df = await safe_akshare_call("stock_individual_info_em", symbol=symbol)

    # 第三步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取股票 {symbol} 的基本信息。请检查股票代码是否正确或稍后重试。"

    if df.empty:
        return f"暂无数据: 股票 {symbol} 的基本信息暂时无法获取。"

    # 第四步：解析数据并格式化
    try:
        # 将 DataFrame 转换为字典，方便查找
        info_dict = {}
        for _, row in df.iterrows():
            item = str(row['item']).strip()
            value = str(row['value']).strip()
            info_dict[item] = value

        # 构建格式化结果
        result = f"=== {symbol} 股票基本信息 ===\n"

        # 基本信息
        stock_name = info_dict.get('股票简称', 'N/A')
        stock_code = info_dict.get('股票代码', symbol)
        latest_price = info_dict.get('最新', 'N/A')

        result += f"股票代码: {stock_code}\n"
        result += f"股票简称: {stock_name}\n"

        # 价格信息
        if latest_price != 'N/A':
            try:
                price_float = float(latest_price)
                result += f"最新价格: {price_float:.2f}元\n"
            except ValueError:
                result += f"最新价格: {latest_price}元\n"
        else:
            result += f"最新价格: 暂无数据\n"

        # 股本信息
        total_shares = info_dict.get('总股本', 'N/A')
        float_shares = info_dict.get('流通股', 'N/A')

        if total_shares != 'N/A':
            try:
                total_shares_float = float(total_shares)
                result += f"总股本: {total_shares_float:,.0f}股\n"
            except ValueError:
                result += f"总股本: {total_shares}股\n"
        else:
            result += f"总股本: 暂无数据\n"

        if float_shares != 'N/A':
            try:
                float_shares_float = float(float_shares)
                result += f"流通股: {float_shares_float:,.0f}股\n"
            except ValueError:
                result += f"流通股: {float_shares}股\n"
        else:
            result += f"流通股: 暂无数据\n"

        # 市值信息
        total_market_cap = info_dict.get('总市值', 'N/A')
        float_market_cap = info_dict.get('流通市值', 'N/A')

        if total_market_cap != 'N/A':
            try:
                total_cap_float = float(total_market_cap)
                result += f"总市值: {total_cap_float:,.0f}元\n"
            except ValueError:
                result += f"总市值: {total_market_cap}元\n"
        else:
            result += f"总市值: 暂无数据\n"

        if float_market_cap != 'N/A':
            try:
                float_cap_float = float(float_market_cap)
                result += f"流通市值: {float_cap_float:,.0f}元\n"
            except ValueError:
                result += f"流通市值: {float_market_cap}元\n"
        else:
            result += f"流通市值: 暂无数据\n"

        # 行业和上市时间
        industry = info_dict.get('行业', 'N/A')
        listing_date = info_dict.get('上市时间', 'N/A')

        result += f"所属行业: {industry}\n"

        if listing_date != 'N/A' and listing_date.isdigit() and len(listing_date) == 8:
            # 格式化上市时间 YYYYMMDD -> YYYY-MM-DD
            formatted_date = f"{listing_date[:4]}-{listing_date[4:6]}-{listing_date[6:8]}"
            result += f"上市时间: {formatted_date}\n"
        else:
            result += f"上市时间: {listing_date}\n"

        # 添加其他可能的信息
        other_fields = ['市盈率', '市净率', '每股收益', '每股净资产', '净资产收益率', '毛利率']
        for field in other_fields:
            if field in info_dict and info_dict[field] != 'N/A':
                result += f"{field}: {info_dict[field]}\n"

        # 添加数据更新时间
        result += f"\n数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result += "\n数据来源: 东方财富"

        return result

    except Exception as e:
        # 如果解析失败，返回原始数据
        print(f"解析股票信息时发生错误: {str(e)}")
        title = f"{symbol} 股票基本信息（原始数据）"
        return format_dataframe_to_string(df, title)


@mcp.tool()
async def get_stock_chip_distribution(symbol: str, adjust: str = "") -> str:
    """获取股票筹码分布数据

    通过 akshare 的 stock_cyq_em 接口获取指定股票的筹码分布数据，
    包括获利比例、平均成本、成本分布区间、集中度等关键指标。
    这是 MCP 工具函数，为 AI 模型提供股票筹码分析能力。

    Args:
        symbol (str): 股票代码，6位数字格式，如 "000001" (平安银行)
        adjust (str, optional): 复权方式. Defaults to "".
            - "": 不复权
            - "qfq": 前复权
            - "hfq": 后复权

    Returns:
        str: 格式化的筹码分布数据字符串，包含：
            - 日期、获利比例、平均成本
            - 90%成本分布区间（低位-高位）、90%集中度
            - 70%成本分布区间（低位-高位）、70%集中度
            - 近期筹码分布趋势分析

    Example:
        >>> await get_stock_chip_distribution("000001")
        "=== 000001 筹码分布数据 ===\\n日期: 2024-01-11, 获利比例: 7.44%, 平均成本: 11.25元\\n..."

        >>> await get_stock_chip_distribution("600519", "qfq")
        "=== 600519 筹码分布数据（前复权） ===\\n日期: 2024-01-11, 获利比例: 15.32%, ..."
    """
    # 第一步：验证股票代码格式
    if not validate_stock_symbol(symbol):
        return f"错误: 股票代码格式无效。请输入6位数字代码，如 '000001'，当前输入: '{symbol}'"

    # 第二步：验证复权方式参数
    valid_adjusts = ["", "qfq", "hfq"]
    if adjust not in valid_adjusts:
        return f"错误: 复权方式无效。支持的方式: {', '.join(valid_adjusts)}，当前输入: '{adjust}'"

    # 第三步：调用 akshare 获取筹码分布数据
    print(f"正在获取股票 {symbol} 的筹码分布数据...")
    df = await safe_akshare_call("stock_cyq_em", symbol=symbol, adjust=adjust)

    # 第四步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取股票 {symbol} 的筹码分布数据。请检查股票代码是否正确或稍后重试。"

    if df.empty:
        return f"暂无数据: 股票 {symbol} 的筹码分布数据暂时无法获取。"

    # 第五步：格式化数据标题
    title = f"{symbol} 筹码分布数据"
    if adjust:
        adjust_name = {"qfq": "前复权", "hfq": "后复权"}[adjust]
        title += f"（{adjust_name}）"

    # 第六步：格式化基础数据（显示最近10条记录）
    recent_df = df.tail(10) if len(df) > 10 else df
    result = format_dataframe_to_string(recent_df, title)

    # 第七步：添加筹码分析
    if not df.empty:
        result += "\n=== 筹码分析 ===\n"

        # 获取最新数据
        latest = df.iloc[-1]
        # latest_date = latest['日期'] if '日期' in df.columns else "最新"

        # 获利比例分析
        profit_ratio = latest.get('获利比例', 0)
        if isinstance(profit_ratio, (int, float)):
            profit_pct = profit_ratio * 100 if profit_ratio <= 1 else profit_ratio
            result += f"最新获利比例: {profit_pct:.2f}%"

            if profit_pct > 80:
                profit_desc = "（高位获利盘较多，存在抛压风险）"
            elif profit_pct > 50:
                profit_desc = "（获利盘适中，市场情绪相对平衡）"
            elif profit_pct > 20:
                profit_desc = "（获利盘较少，上涨阻力相对较小）"
            else:
                profit_desc = "（大部分投资者处于亏损状态）"

            result += profit_desc + "\n"

        # 平均成本分析
        avg_cost = latest.get('平均成本', 0)
        if isinstance(avg_cost, (int, float)) and avg_cost > 0:
            result += f"平均成本: {avg_cost:.2f}元\n"

        # 90%成本分布分析
        cost_90_low = latest.get('90成本-低', 0)
        cost_90_high = latest.get('90成本-高', 0)
        concentration_90 = latest.get('90集中度', 0)

        if all(isinstance(x, (int, float)) and x > 0 for x in [cost_90_low, cost_90_high, concentration_90]):
            cost_range_90 = cost_90_high - cost_90_low
            result += f"90%成本分布: {cost_90_low:.2f}元 - {cost_90_high:.2f}元"
            result += f"（区间: {cost_range_90:.2f}元）\n"
            result += f"90%集中度: {concentration_90:.4f}"

            if concentration_90 > 0.15:
                concentration_desc = "（筹码高度集中，波动性较大）"
            elif concentration_90 > 0.10:
                concentration_desc = "（筹码相对集中）"
            else:
                concentration_desc = "（筹码分散，相对稳定）"

            result += concentration_desc + "\n"

        # 70%成本分布分析
        cost_70_low = latest.get('70成本-低', 0)
        cost_70_high = latest.get('70成本-高', 0)
        concentration_70 = latest.get('70集中度', 0)

        if all(isinstance(x, (int, float)) and x > 0 for x in [cost_70_low, cost_70_high, concentration_70]):
            cost_range_70 = cost_70_high - cost_70_low
            result += f"70%成本分布: {cost_70_low:.2f}元 - {cost_70_high:.2f}元"
            result += f"（区间: {cost_range_70:.2f}元）\n"
            result += f"70%集中度: {concentration_70:.4f}\n"

        # 趋势分析（对比前一交易日）
        if len(df) >= 2:
            previous = df.iloc[-2]
            prev_profit = previous.get('获利比例', 0)
            prev_avg_cost = previous.get('平均成本', 0)

            result += "\n=== 趋势变化 ===\n"

            # 获利比例变化
            if isinstance(prev_profit, (int, float)) and isinstance(profit_ratio, (int, float)):
                profit_change = (profit_ratio - prev_profit) * 100 if profit_ratio <= 1 else profit_ratio - prev_profit
                if abs(profit_change) > 0.01:
                    change_direction = "上升" if profit_change > 0 else "下降"
                    result += f"获利比例较前日{change_direction} {abs(profit_change):.2f}个百分点\n"

            # 平均成本变化
            if isinstance(prev_avg_cost, (int, float)) and isinstance(avg_cost, (int, float)) and prev_avg_cost > 0:
                cost_change = avg_cost - prev_avg_cost
                cost_change_pct = (cost_change / prev_avg_cost) * 100
                if abs(cost_change_pct) > 0.1:
                    change_direction = "上升" if cost_change > 0 else "下降"
                    result += f"平均成本较前日{change_direction} {abs(cost_change):.2f}元 ({abs(cost_change_pct):.2f}%)\n"

    # 第八步：添加数据统计信息
    result += f"\n数据统计: 共 {len(df)} 个交易日的筹码分布数据"
    if not df.empty:
        start_date = df.iloc[0]['日期'] if '日期' in df.columns else "未知"
        end_date = df.iloc[-1]['日期'] if '日期' in df.columns else "未知"
        result += f"，时间范围: {start_date} 至 {end_date}"

    result += "\n数据来源: 东方财富（近90个交易日）"

    return result


@mcp.tool()
async def search_stock_code(query: str) -> str:
    """股票代码和名称互查

    通过 akshare 的 stock_info_a_code_name 接口实现股票代码和名称的双向查询功能。
    支持根据股票代码查询名称，或根据股票名称查询代码。
    这是 MCP 工具函数，为 AI 模型提供股票代码查询能力。

    Args:
        query (str): 查询内容，可以是：
            - 股票代码：6位数字，如 "000001"、"600519"
            - 股票名称：中文名称，如 "平安银行"、"贵州茅台"
            - 名称关键词：部分名称，如 "平安"、"茅台"

    Returns:
        str: 格式化的查询结果字符串，包含：
            - 匹配的股票代码和名称
            - 所属市场（上海/深圳/北京）
            - 匹配数量和相关建议

    Example:
        >>> await search_stock_code("000001")
        "=== 股票查询结果 ===\\n代码: 000001, 名称: 平安银行, 市场: 深圳\\n"

        >>> await search_stock_code("平安银行")
        "=== 股票查询结果 ===\\n代码: 000001, 名称: 平安银行, 市场: 深圳\\n"

        >>> await search_stock_code("平安")
        "=== 股票查询结果 ===\\n找到 3 只相关股票:\\n1. 000001 平安银行\\n2. 601318 中国平安\\n..."
    """
    # 第一步：验证查询参数
    if not query or not query.strip():
        return "错误: 查询内容不能为空。请输入股票代码或名称。"

    query = query.strip()

    # 第二步：获取股票代码名称对照表
    print(f"正在查询股票: {query}")
    df = await safe_akshare_call("stock_info_a_code_name")

    # 第三步：检查数据获取结果
    if df is None:
        return "错误: 无法获取股票代码名称数据。请稍后重试。"

    if df.empty:
        return "错误: 股票代码名称数据为空。"

    # 第四步：判断查询类型并进行搜索
    # 检查是否为6位数字的股票代码
    if len(query) == 6 and query.isdigit():
        # 按股票代码精确查询
        matched = df[df['code'] == query]

        if not matched.empty:
            row = matched.iloc[0]
            code = row['code']
            name = row['name']

            # 判断市场
            if code.startswith(('000', '001', '002', '003', '300')):
                market_full = "深圳证券交易所"
            elif code.startswith(('600', '601', '603', '688')):
                market_full = "上海证券交易所"
            elif code.startswith(('8', '4')):
                market_full = "北京证券交易所"
            else:
                market_full = "未知交易所"

            result = f"=== 股票查询结果 ===\n"
            result += f"股票代码: {code}\n"
            result += f"股票名称: {name}\n"
            result += f"所属市场: {market_full}\n"

            return result
        else:
            return f"未找到股票代码 '{query}' 对应的股票。请检查代码是否正确。"

    else:
        # 按股票名称模糊查询
        # 模糊匹配股票名称
        matched = df[df['name'].str.contains(query, na=False)]

        if matched.empty:
            return f"未找到包含 '{query}' 的股票。请尝试其他关键词。"

        # 限制返回结果数量
        max_results = 10
        original_count = len(matched)
        if len(matched) > max_results:
            matched = matched.head(max_results)
            show_more = True
        else:
            show_more = False

        result = f"=== 股票查询结果 ===\n"

        if len(matched) == 1:
            # 单个结果，显示详细信息
            row = matched.iloc[0]
            code = row['code']
            name = row['name']

            # 判断市场
            if code.startswith(('000', '001', '002', '003', '300')):
                market_full = "深圳证券交易所"
            elif code.startswith(('600', '601', '603', '688')):
                market_full = "上海证券交易所"
            elif code.startswith(('8', '4')):
                market_full = "北京证券交易所"
            else:
                market_full = "未知交易所"

            result += f"股票代码: {code}\n"
            result += f"股票名称: {name}\n"
            result += f"所属市场: {market_full}\n"

        else:
            # 多个结果，显示列表
            result += f"找到 {len(matched)} 只相关股票:\n\n"
            result += "序号  代码    股票名称        市场\n"
            result += "-" * 35 + "\n"

            for idx, (_, row) in enumerate(matched.iterrows(), 1):
                code = row['code']
                name = row['name']

                # 判断市场简称
                if code.startswith(('000', '001', '002', '003', '300')):
                    market_short = "深圳"
                elif code.startswith(('600', '601', '603', '688')):
                    market_short = "上海"
                elif code.startswith(('8', '4')):
                    market_short = "北京"
                else:
                    market_short = "未知"

                result += f"{idx:2d}    {code}  {name:12s}  {market_short}\n"

            if show_more:
                result += f"\n注意: 共找到 {original_count} 只股票，仅显示前 {max_results} 只。\n"
                result += "请使用更具体的关键词缩小搜索范围。\n"

        # 添加数据说明
        result += f"\n数据来源: akshare (沪深京A股)"
        result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return result


@mcp.tool()
async def get_stock_hot_rank() -> str:
    """获取股票热度排行榜

    通过 akshare 的 stock_hot_rank_em 接口获取东方财富网站的股票人气排行榜。
    返回当前交易日前100个股票的人气排名数据。
    这是 MCP 工具函数，为 AI 模型提供股票热度分析能力。

    Returns:
        str: 格式化的股票热度排行榜字符串，包含：
            - 排名、股票代码、股票名称
            - 最新价格、涨跌幅、涨跌额
            - 成交量、成交额、人气值等

    Example:
        >>> await get_stock_hot_rank()
        "=== 股票热度排行榜（前100名） ===\\n1. 000001 平安银行: 10.50元 (+1.23%) 人气值: 12345\\n..."
    """
    # 第一步：调用 akshare 获取股票热度数据
    print("正在获取股票热度排行榜...")
    df = await safe_akshare_call("stock_hot_rank_em")

    # 第二步：检查数据获取结果
    if df is None:
        return "错误: 无法获取股票热度数据。请稍后重试。"

    if df.empty:
        return "暂无数据: 股票热度排行榜暂时无数据。"

    # 第三步：格式化数据
    title = "股票热度排行榜（前100名）"
    result = f"=== {title} ===\n\n"
    result += "排名  代码    股票名称      最新价    涨跌幅    人气值\n"
    result += "-" * 55 + "\n"

    # 显示前20名热门股票
    display_count = min(20, len(df))
    for i in range(display_count):
        row = df.iloc[i]

        # 获取基本信息
        rank = i + 1
        code = row.get('代码', 'N/A')
        name = row.get('名称', 'N/A')
        price = row.get('最新价', 0)
        change_pct = row.get('涨跌幅', 0)
        popularity = row.get('人气', 0)

        # 格式化显示
        # 安全格式化价格
        price_str = f"{price:7.2f}" if isinstance(price, (int, float)) else f"{str(price):>7s}"
        result += f"{rank:3d}   {str(code)}  {str(name):10s}  {price_str}元  "

        # 涨跌幅颜色标识
        if isinstance(change_pct, (int, float)):
            if change_pct > 0:
                result += f"+{change_pct:5.2f}%📈  "
            elif change_pct < 0:
                result += f"{change_pct:6.2f}%📉  "
            else:
                result += f" {change_pct:5.2f}%➡️  "
        else:
            result += f"{str(change_pct):>7s}   "

        # 人气值处理
        if isinstance(popularity, (int, float)):
            result += f"{popularity:>8.0f}\n"
        else:
            result += f"{str(popularity):>8s}\n"

    # 第四步：添加统计信息
    if not df.empty:
        result += f"\n=== 热度分析 ===\n"

        # 涨跌统计
        if '涨跌幅' in df.columns:
            rising_count = len(df[df['涨跌幅'] > 0])
            falling_count = len(df[df['涨跌幅'] < 0])
            flat_count = len(df[df['涨跌幅'] == 0])

            result += f"上涨股票: {rising_count}只\n"
            result += f"下跌股票: {falling_count}只\n"
            result += f"平盘股票: {flat_count}只\n"

        # 热度分析
        result += f"\n💡 热度说明:\n"
        result += f"- 排名基于东方财富网股吧的关注度和讨论热度\n"
        result += f"- 热度高的股票通常受到更多投资者关注\n"
        result += f"- 建议结合基本面和技术面进行综合分析\n"

    # 第五步：添加数据说明
    result += f"\n数据统计: 共 {len(df)} 只热门股票"
    result += f"\n数据来源: 东方财富网股吧"
    result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return result


@mcp.tool()
async def get_individual_fund_flow(symbol: str = "即时") -> str:
    """获取个股资金流向数据

    通过 akshare 的 stock_fund_flow_individual 接口获取同花顺个股资金流向数据。
    支持即时数据和不同时间周期的排行榜。
    这是 MCP 工具函数，为 AI 模型提供个股资金流分析能力。

    Args:
        symbol (str, optional): 查询类型. Defaults to "即时".
            - "即时": 当前实时资金流向
            - "3日排行": 3日资金流向排行
            - "5日排行": 5日资金流向排行
            - "10日排行": 10日资金流向排行
            - "20日排行": 20日资金流向排行

    Returns:
        str: 格式化的个股资金流向数据字符串，包含：
            - 股票代码、名称、最新价格、涨跌幅
            - 主力净流入、超大单净流入、大单净流入
            - 中单净流入、小单净流入等资金流向数据

    Example:
        >>> await get_individual_fund_flow("即时")
        "=== 个股资金流向（即时） ===\\n1. 000001 平安银行: 主力净流入 1.23亿元\\n..."

        >>> await get_individual_fund_flow("3日排行")
        "=== 个股资金流向（3日排行） ===\\n1. 600519 贵州茅台: 3日主力净流入 5.67亿元\\n..."
    """
    # 第一步：验证查询类型参数
    valid_symbols = ["即时", "3日排行", "5日排行", "10日排行", "20日排行"]
    if symbol not in valid_symbols:
        return f"错误: 查询类型无效。支持的类型: {', '.join(valid_symbols)}，当前输入: '{symbol}'"

    # 第二步：调用 akshare 获取个股资金流数据
    print(f"正在获取个股资金流向数据（{symbol}）...")
    df = await safe_akshare_call("stock_fund_flow_individual", symbol=symbol)

    # 第三步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取个股资金流向数据（{symbol}）。请稍后重试。"

    if df.empty:
        return f"暂无数据: 个股资金流向数据（{symbol}）暂时无数据。"

    # 第四步：格式化数据
    title = f"个股资金流向（{symbol}）"
    result = f"=== {title} ===\n\n"

    # 显示前30只股票
    display_count = min(30, len(df))

    if symbol == "即时":
        result += "排名  代码    股票名称      最新价    涨跌幅    主力净流入\n"
        result += "-" * 60 + "\n"

        for i in range(display_count):
            row = df.iloc[i]

            rank = i + 1
            code = row.get('代码', 'N/A')
            name = row.get('名称', 'N/A')
            price = row.get('最新价', 0)
            change_pct = row.get('涨跌幅', 0)
            main_flow = row.get('主力净流入-净额', 0)

            # 安全格式化价格
            price_str = f"{price:7.2f}" if isinstance(price, (int, float)) else f"{str(price):>7s}"
            result += f"{rank:3d}   {str(code)}  {str(name):10s}  {price_str}元  "

            # 涨跌幅
            if isinstance(change_pct, (int, float)):
                if change_pct > 0:
                    result += f"+{change_pct:5.2f}%  "
                else:
                    result += f"{change_pct:6.2f}%  "
            else:
                result += f"{str(change_pct):>7s}  "

            # 主力净流入
            if isinstance(main_flow, (int, float)):
                if main_flow > 0:
                    result += f"+{main_flow/100000000:.2f}亿📈\n"
                else:
                    result += f"{main_flow/100000000:.2f}亿📉\n"
            else:
                result += f"{str(main_flow):>10s}\n"

    else:
        # 排行榜数据
        result += "排名  代码    股票名称      涨跌幅    主力净流入    成交额\n"
        result += "-" * 65 + "\n"

        for i in range(display_count):
            row = df.iloc[i]

            rank = i + 1
            code = row.get('代码', 'N/A')
            name = row.get('名称', 'N/A')
            change_pct = row.get('涨跌幅', 0)
            main_flow = row.get('主力净流入-净额', 0)
            volume = row.get('成交额', 0)

            result += f"{rank:3d}   {code}  {str(name):10s}  "

            # 涨跌幅
            if isinstance(change_pct, (int, float)):
                if change_pct > 0:
                    result += f"+{change_pct:5.2f}%  "
                else:
                    result += f"{change_pct:6.2f}%  "
            else:
                result += f"{str(change_pct):>7s}  "

            # 主力净流入
            if isinstance(main_flow, (int, float)):
                result += f"{main_flow/100000000:8.2f}亿  "
            else:
                result += f"{str(main_flow):>10s}  "

            # 成交额
            if isinstance(volume, (int, float)):
                result += f"{volume/100000000:6.2f}亿\n"
            else:
                result += f"{str(volume):>8s}\n"

    # 第五步：添加资金流分析
    if not df.empty and '主力净流入-净额' in df.columns:
        result += f"\n=== 资金流分析 ===\n"

        # 统计净流入和净流出股票数量
        main_flow_data = df['主力净流入-净额'].dropna()
        if not main_flow_data.empty:
            inflow_count = len(main_flow_data[main_flow_data > 0])
            outflow_count = len(main_flow_data[main_flow_data < 0])

            result += f"主力净流入股票: {inflow_count}只\n"
            result += f"主力净流出股票: {outflow_count}只\n"

            # 总体资金流向
            total_flow = main_flow_data.sum()
            if total_flow > 0:
                result += f"整体资金流向: 净流入 {total_flow/100000000:.2f}亿元\n"
            else:
                result += f"整体资金流向: 净流出 {abs(total_flow)/100000000:.2f}亿元\n"

    # 第六步：添加数据说明
    result += f"\n数据统计: 共 {len(df)} 只股票"
    result += f"\n数据来源: 同花顺资金流向"
    result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return result


@mcp.tool()
async def get_concept_fund_flow(symbol: str = "即时") -> str:
    """获取概念资金流向数据

    通过 akshare 的 stock_fund_flow_concept 接口获取同花顺概念资金流向数据。
    支持即时数据和不同时间周期的排行榜。
    这是 MCP 工具函数，为 AI 模型提供概念板块资金流分析能力。

    Args:
        symbol (str, optional): 查询类型. Defaults to "即时".
            - "即时": 当前实时概念资金流向
            - "3日排行": 3日概念资金流向排行
            - "5日排行": 5日概念资金流向排行
            - "10日排行": 10日概念资金流向排行
            - "20日排行": 20日概念资金流向排行

    Returns:
        str: 格式化的概念资金流向数据字符串，包含：
            - 概念名称、概念指数、涨跌幅
            - 流入资金、流出资金、净额
            - 公司家数、领涨股等信息

    Example:
        >>> await get_concept_fund_flow("即时")
        "=== 概念资金流向（即时） ===\\n1. 人工智能: 净流入 12.34亿元 (+3.45%)\\n..."
    """
    # 第一步：验证查询类型参数
    valid_symbols = ["即时", "3日排行", "5日排行", "10日排行", "20日排行"]
    if symbol not in valid_symbols:
        return f"错误: 查询类型无效。支持的类型: {', '.join(valid_symbols)}，当前输入: '{symbol}'"

    # 第二步：调用 akshare 获取概念资金流数据
    print(f"正在获取概念资金流向数据（{symbol}）...")
    df = await safe_akshare_call("stock_fund_flow_concept", symbol=symbol)

    # 第三步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取概念资金流向数据（{symbol}）。请稍后重试。"

    if df.empty:
        return f"暂无数据: 概念资金流向数据（{symbol}）暂时无数据。"

    # 第四步：格式化数据
    title = f"概念资金流向（{symbol}）"
    result = f"=== {title} ===\n\n"
    result += "排名  概念名称          涨跌幅    净流入    公司数  领涨股\n"
    result += "-" * 65 + "\n"

    # 显示前20个概念
    display_count = min(20, len(df))
    for i in range(display_count):
        row = df.iloc[i]

        rank = i + 1
        concept = row.get('行业', 'N/A')
        change_pct = row.get('行业-涨跌幅', 0)
        net_flow = row.get('净额', 0)
        company_count = row.get('公司家数', 0)
        leader = row.get('领涨股', 'N/A')

        result += f"{rank:3d}   {str(concept):15s}  "

        # 涨跌幅
        if isinstance(change_pct, (int, float)):
            if change_pct > 0:
                result += f"+{change_pct:5.2f}%  "
            else:
                result += f"{change_pct:6.2f}%  "
        else:
            result += f"{str(change_pct):>7s}  "

        # 净流入
        if isinstance(net_flow, (int, float)):
            if net_flow > 0:
                result += f"+{net_flow:6.2f}亿  "
            else:
                result += f"{net_flow:7.2f}亿  "
        else:
            result += f"{str(net_flow):>9s}  "

        # 公司数和领涨股
        company_str = f"{company_count:4.0f}" if isinstance(company_count, (int, float)) else str(company_count)
        result += f"{company_str}家  {str(leader)}\n"

    # 第五步：添加概念分析
    if not df.empty:
        result += f"\n=== 概念分析 ===\n"

        # 统计涨跌概念数量
        if '行业-涨跌幅' in df.columns:
            rising_concepts = len(df[df['行业-涨跌幅'] > 0])
            falling_concepts = len(df[df['行业-涨跌幅'] < 0])

            result += f"上涨概念: {rising_concepts}个\n"
            result += f"下跌概念: {falling_concepts}个\n"

        # 资金流向统计
        if '净额' in df.columns:
            inflow_concepts = len(df[df['净额'] > 0])
            outflow_concepts = len(df[df['净额'] < 0])
            total_net_flow = df['净额'].sum()

            result += f"净流入概念: {inflow_concepts}个\n"
            result += f"净流出概念: {outflow_concepts}个\n"
            result += f"概念板块总净流入: {total_net_flow:.2f}亿元\n"

        # 热门概念提示
        result += f"\n💡 投资提示:\n"
        result += f"- 概念板块资金流向反映市场热点和投资偏好\n"
        result += f"- 净流入较大的概念通常受到资金追捧\n"
        result += f"- 建议关注领涨股的基本面和技术面\n"

    # 第六步：添加数据说明
    result += f"\n数据统计: 共 {len(df)} 个概念板块"
    result += f"\n数据来源: 同花顺概念资金流"
    result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return result


@mcp.tool()
async def get_industry_fund_flow(symbol: str = "即时") -> str:
    """获取行业资金流向数据

    通过 akshare 的 stock_fund_flow_industry 接口获取同花顺行业资金流向数据。
    支持即时数据和不同时间周期的排行榜。
    这是 MCP 工具函数，为 AI 模型提供行业板块资金流分析能力。

    Args:
        symbol (str, optional): 查询类型. Defaults to "即时".
            - "即时": 当前实时行业资金流向
            - "3日排行": 3日行业资金流向排行
            - "5日排行": 5日行业资金流向排行
            - "10日排行": 10日行业资金流向排行
            - "20日排行": 20日行业资金流向排行

    Returns:
        str: 格式化的行业资金流向数据字符串，包含：
            - 行业名称、行业指数、涨跌幅
            - 流入资金、流出资金、净额
            - 公司家数、领涨股等信息

    Example:
        >>> await get_industry_fund_flow("即时")
        "=== 行业资金流向（即时） ===\\n1. 电子信息: 净流入 8.76亿元 (+2.15%)\\n..."
    """
    # 第一步：验证查询类型参数
    valid_symbols = ["即时", "3日排行", "5日排行", "10日排行", "20日排行"]
    if symbol not in valid_symbols:
        return f"错误: 查询类型无效。支持的类型: {', '.join(valid_symbols)}，当前输入: '{symbol}'"

    # 第二步：调用 akshare 获取行业资金流数据
    print(f"正在获取行业资金流向数据（{symbol}）...")
    df = await safe_akshare_call("stock_fund_flow_industry", symbol=symbol)

    # 第三步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取行业资金流向数据（{symbol}）。请稍后重试。"

    if df.empty:
        return f"暂无数据: 行业资金流向数据（{symbol}）暂时无数据。"

    # 第四步：格式化数据
    title = f"行业资金流向（{symbol}）"
    result = f"=== {title} ===\n\n"
    result += "排名  行业名称          涨跌幅    净流入    公司数  领涨股\n"
    result += "-" * 65 + "\n"

    # 显示所有行业（通常不超过100个）
    display_count = min(30, len(df))
    for i in range(display_count):
        row = df.iloc[i]

        rank = i + 1
        industry = row.get('行业', 'N/A')
        change_pct = row.get('行业-涨跌幅', 0)
        net_flow = row.get('净额', 0)
        company_count = row.get('公司家数', 0)
        leader = row.get('领涨股', 'N/A')

        result += f"{rank:3d}   {str(industry):15s}  "

        # 涨跌幅处理（可能是字符串格式）
        if isinstance(change_pct, str):
            try:
                change_pct = float(change_pct.replace('%', ''))
            except:
                pass

        if isinstance(change_pct, (int, float)):
            if change_pct > 0:
                result += f"+{change_pct:5.2f}%  "
            else:
                result += f"{change_pct:6.2f}%  "
        else:
            result += f"{str(change_pct):>7s}  "

        # 净流入
        if isinstance(net_flow, (int, float)):
            if net_flow > 0:
                result += f"+{net_flow:6.2f}亿  "
            else:
                result += f"{net_flow:7.2f}亿  "
        else:
            result += f"{str(net_flow):>9s}  "

        # 公司数和领涨股
        company_str = f"{company_count:4.0f}" if isinstance(company_count, (int, float)) else str(company_count)
        result += f"{company_str}家  {str(leader)}\n"

    # 第五步：添加行业分析
    if not df.empty:
        result += f"\n=== 行业分析 ===\n"

        # 统计涨跌行业数量
        if '行业-涨跌幅' in df.columns:
            # 处理可能的字符串格式
            change_data = df['行业-涨跌幅'].copy()
            if change_data.dtype == 'object':
                change_data = pd.to_numeric(change_data.astype(str).str.replace('%', ''), errors='coerce')

            rising_industries = len(change_data[change_data > 0])
            falling_industries = len(change_data[change_data < 0])

            result += f"上涨行业: {rising_industries}个\n"
            result += f"下跌行业: {falling_industries}个\n"

        # 资金流向统计
        if '净额' in df.columns:
            inflow_industries = len(df[df['净额'] > 0])
            outflow_industries = len(df[df['净额'] < 0])
            total_net_flow = df['净额'].sum()

            result += f"净流入行业: {inflow_industries}个\n"
            result += f"净流出行业: {outflow_industries}个\n"
            result += f"行业板块总净流入: {total_net_flow:.2f}亿元\n"

        # 投资建议
        result += f"\n💡 投资建议:\n"
        result += f"- 行业资金流向体现产业投资趋势\n"
        result += f"- 净流入较大的行业可能存在投资机会\n"
        result += f"- 建议结合宏观经济和政策导向分析\n"

    # 第六步：添加数据说明
    result += f"\n数据统计: 共 {len(df)} 个行业板块"
    result += f"\n数据来源: 同花顺行业资金流"
    result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return result


@mcp.tool()
async def get_industry_board_overview() -> str:
    """获取行业板块总览

    通过 akshare 的 stock_board_industry_summary_ths 接口获取同花顺行业板块总览数据。
    返回当前时刻所有行业板块的综合表现情况。
    这是 MCP 工具函数，为 AI 模型提供行业板块全景分析能力。

    Returns:
        str: 格式化的行业板块总览字符串，包含：
            - 板块名称、涨跌幅、总成交量、总成交额
            - 净流入、上涨家数、下跌家数、均价
            - 领涨股及其涨跌幅等综合信息

    Example:
        >>> await get_industry_board_overview()
        "=== 行业板块总览 ===\\n1. 电子信息: +3.45% 净流入12.34亿 领涨股: 某某科技\\n..."
    """
    # 第一步：调用 akshare 获取行业板块总览数据
    print("正在获取行业板块总览数据...")
    df = await safe_akshare_call("stock_board_industry_summary_ths")

    # 第二步：检查数据获取结果
    if df is None:
        return "错误: 无法获取行业板块总览数据。请稍后重试。"

    if df.empty:
        return "暂无数据: 行业板块总览数据暂时无数据。"

    # 第三步：格式化数据
    title = "行业板块总览"
    result = f"=== {title} ===\n\n"
    result += "排名  板块名称          涨跌幅    成交额    净流入    涨/跌    领涨股\n"
    result += "-" * 80 + "\n"

    # 显示前30个板块
    display_count = min(30, len(df))
    for i in range(display_count):
        row = df.iloc[i]

        rank = i + 1
        board = row.get('板块', 'N/A')
        change_pct = row.get('涨跌幅', 0)
        volume = row.get('总成交额', 0)
        net_flow = row.get('净流入', 0)
        up_count = row.get('上涨家数', 0)
        down_count = row.get('下跌家数', 0)
        leader = row.get('领涨股', 'N/A')
        leader_change = row.get('领涨股-涨跌幅', 0)

        result += f"{rank:3d}   {str(board):15s}  "

        # 涨跌幅处理（可能是字符串格式）
        if isinstance(change_pct, str):
            try:
                change_pct_num = float(change_pct.replace('%', ''))
                if change_pct_num > 0:
                    result += f"+{change_pct:>6s}📈  "
                elif change_pct_num < 0:
                    result += f"{change_pct:>7s}📉  "
                else:
                    result += f"{change_pct:>7s}➡️  "
            except:
                result += f"{change_pct:>8s}  "
        else:
            if change_pct > 0:
                result += f"+{change_pct:5.2f}%📈  "
            elif change_pct < 0:
                result += f"{change_pct:6.2f}%📉  "
            else:
                result += f" {change_pct:5.2f}%➡️  "

        # 成交额
        if isinstance(volume, (int, float)):
            result += f"{volume:7.1f}亿  "
        else:
            result += f"{str(volume):>9s}  "

        # 净流入
        if isinstance(net_flow, (int, float)):
            if net_flow > 0:
                result += f"+{net_flow:5.1f}亿  "
            else:
                result += f"{net_flow:6.1f}亿  "
        else:
            result += f"{str(net_flow):>8s}  "

        # 涨跌家数
        up_str = f"{up_count:3.0f}" if isinstance(up_count, (int, float)) else str(up_count)
        down_str = f"{down_count:3.0f}" if isinstance(down_count, (int, float)) else str(down_count)
        result += f"{up_str}/{down_str}  "

        # 领涨股
        if str(leader) != 'N/A' and isinstance(leader_change, (int, float)) and leader_change != 0:
            result += f"{str(leader)}({leader_change:+.1f}%)\n"
        else:
            result += f"{str(leader)}\n"

    # 第四步：添加市场分析
    if not df.empty:
        result += f"\n=== 市场分析 ===\n"

        # 板块涨跌统计
        if '涨跌幅' in df.columns:
            # 处理涨跌幅数据
            change_data = df['涨跌幅'].copy()
            if change_data.dtype == 'object':
                change_data = pd.to_numeric(change_data.astype(str).str.replace('%', ''), errors='coerce')

            rising_boards = len(change_data[change_data > 0])
            falling_boards = len(change_data[change_data < 0])
            flat_boards = len(change_data[change_data == 0])

            result += f"上涨板块: {rising_boards}个\n"
            result += f"下跌板块: {falling_boards}个\n"
            result += f"平盘板块: {flat_boards}个\n"

            # 市场情绪
            if rising_boards > falling_boards:
                market_sentiment = "偏多"
                sentiment_emoji = "📈"
            elif rising_boards < falling_boards:
                market_sentiment = "偏空"
                sentiment_emoji = "📉"
            else:
                market_sentiment = "平衡"
                sentiment_emoji = "➡️"

            result += f"市场情绪: {market_sentiment} {sentiment_emoji}\n"

        # 资金流向统计
        if '净流入' in df.columns:
            inflow_boards = len(df[df['净流入'] > 0])
            outflow_boards = len(df[df['净流入'] < 0])
            total_net_flow = df['净流入'].sum()

            result += f"净流入板块: {inflow_boards}个\n"
            result += f"净流出板块: {outflow_boards}个\n"
            result += f"市场总净流入: {total_net_flow:.1f}亿元\n"

        # 成交活跃度
        if '总成交额' in df.columns:
            total_volume = df['总成交额'].sum()
            avg_volume = df['总成交额'].mean()
            result += f"市场总成交额: {total_volume:.1f}亿元\n"
            result += f"板块平均成交额: {avg_volume:.1f}亿元\n"

        # 投资建议
        result += f"\n💡 投资策略:\n"
        result += f"- 关注净流入较大且涨幅居前的板块\n"
        result += f"- 注意领涨股的持续性和基本面支撑\n"
        result += f"- 结合宏观政策和行业景气度进行配置\n"
        result += f"- 控制仓位，注意风险管理\n"

    # 第五步：添加数据说明
    result += f"\n数据统计: 共 {len(df)} 个行业板块"
    result += f"\n数据来源: 同花顺行业板块"
    result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return result


@mcp.tool()
async def get_dragon_tiger_list(start_date: str = "", end_date: str = "") -> str:
    """获取龙虎榜详情数据

    通过 akshare 的 stock_lhb_detail_em 接口获取东方财富网龙虎榜详情数据。
    龙虎榜反映了大额交易和异常波动股票的详细交易信息，是重要的市场参考指标。
    这是 MCP 工具函数，为 AI 模型提供龙虎榜分析能力。

    Args:
        start_date (str, optional): 开始日期，格式 "YYYYMMDD". Defaults to "".
            如果为空，则获取最近7天的数据
        end_date (str, optional): 结束日期，格式 "YYYYMMDD". Defaults to "".
            如果为空，则使用今天的日期

    Returns:
        str: 格式化的龙虎榜详情数据字符串，包含：
            - 股票代码、名称、上榜日期、解读
            - 收盘价、涨跌幅、龙虎榜净买额
            - 龙虎榜买入额、卖出额、成交额
            - 净买额占比、成交额占比、换手率
            - 上榜原因、上榜后表现等信息

    Example:
        >>> await get_dragon_tiger_list("20240401", "20240407")
        "=== 龙虎榜详情（2024-04-01 至 2024-04-07） ===\\n1. 000001 平安银行: 净买额 1.23亿元\\n..."

        >>> await get_dragon_tiger_list()
        "=== 龙虎榜详情（最近7天） ===\\n1. 600519 贵州茅台: 净买额 5.67亿元\\n..."
    """
    # 第一步：处理日期参数
    if not start_date or not end_date:
        # 如果没有指定日期，获取最近7天的数据
        from datetime import datetime, timedelta

        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        if not start_date:
            start_datetime = datetime.now() - timedelta(days=7)
            start_date = start_datetime.strftime("%Y%m%d")

    # 第二步：验证日期格式
    try:
        start_formatted = format_date_string(start_date)
        end_formatted = format_date_string(end_date)
    except ValueError as e:
        return f"错误: {str(e)}"

    # 第三步：调用 akshare 获取龙虎榜数据
    print(f"正在获取龙虎榜详情数据（{start_formatted} 至 {end_formatted}）...")
    df = await safe_akshare_call("stock_lhb_detail_em", start_date=start_date, end_date=end_date)

    # 第四步：检查数据获取结果
    if df is None:
        return f"错误: 无法获取龙虎榜详情数据。请稍后重试。"

    if df.empty:
        return f"暂无数据: {start_formatted} 至 {end_formatted} 期间没有龙虎榜数据。"

    # 第五步：格式化数据标题
    if start_date == end_date:
        title = f"龙虎榜详情（{start_formatted}）"
    else:
        title = f"龙虎榜详情（{start_formatted} 至 {end_formatted}）"

    result = f"=== {title} ===\n\n"

    # 第六步：按日期分组显示数据
    if '上榜日' in df.columns:
        # 按上榜日期分组
        grouped = df.groupby('上榜日')

        for date, group in grouped:
            result += f"📅 {date} ({len(group)}只股票上榜)\n"
            result += "-" * 80 + "\n"
            result += "序号  代码    股票名称      涨跌幅    净买额    成交额占比  上榜原因\n"
            result += "-" * 80 + "\n"

            # 显示当日上榜股票（最多20只）
            display_count = min(20, len(group))
            for i in range(display_count):
                row = group.iloc[i]

                seq = i + 1
                code = str(row.get('代码', 'N/A'))
                name = str(row.get('名称', 'N/A'))
                change_pct = row.get('涨跌幅', 0)
                net_buy = row.get('龙虎榜净买额', 0)
                volume_ratio = row.get('成交额占总成交比', 0)
                reason = str(row.get('上榜原因', 'N/A'))

                result += f"{seq:3d}   {code}  {name:10s}  "

                # 涨跌幅
                if isinstance(change_pct, (int, float)):
                    if change_pct > 0:
                        result += f"+{change_pct:5.2f}%📈  "
                    elif change_pct < 0:
                        result += f"{change_pct:6.2f}%📉  "
                    else:
                        result += f" {change_pct:5.2f}%➡️  "
                else:
                    result += f"{str(change_pct):>8s}  "

                # 净买额（转换为亿元）
                if isinstance(net_buy, (int, float)):
                    net_buy_yi = net_buy / 100000000
                    if net_buy_yi > 0:
                        result += f"+{net_buy_yi:5.2f}亿  "
                    else:
                        result += f"{net_buy_yi:6.2f}亿  "
                else:
                    result += f"{str(net_buy):>8s}  "

                # 成交额占比
                if isinstance(volume_ratio, (int, float)):
                    result += f"{volume_ratio:5.2f}%  "
                else:
                    result += f"{str(volume_ratio):>6s}  "

                # 上榜原因（截取前15个字符）
                reason_short = reason[:15] + "..." if len(reason) > 15 else reason
                result += f"{reason_short}\n"

            if len(group) > display_count:
                result += f"... 还有 {len(group) - display_count} 只股票\n"

            result += "\n"

    else:
        # 如果没有上榜日列，直接显示所有数据
        result += "代码    股票名称      上榜日      涨跌幅    净买额    上榜原因\n"
        result += "-" * 75 + "\n"

        display_count = min(50, len(df))
        for i in range(display_count):
            row = df.iloc[i]

            code = str(row.get('代码', 'N/A'))
            name = str(row.get('名称', 'N/A'))
            date = str(row.get('上榜日', 'N/A'))
            change_pct = row.get('涨跌幅', 0)
            net_buy = row.get('龙虎榜净买额', 0)
            reason = str(row.get('上榜原因', 'N/A'))

            result += f"{code}  {name:10s}  {date}  "

            # 涨跌幅
            if isinstance(change_pct, (int, float)):
                if change_pct > 0:
                    result += f"+{change_pct:5.2f}%  "
                else:
                    result += f"{change_pct:6.2f}%  "
            else:
                result += f"{str(change_pct):>7s}  "

            # 净买额
            if isinstance(net_buy, (int, float)):
                net_buy_yi = net_buy / 100000000
                result += f"{net_buy_yi:6.2f}亿  "
            else:
                result += f"{str(net_buy):>8s}  "

            # 上榜原因
            reason_short = reason[:20] + "..." if len(reason) > 20 else reason
            result += f"{reason_short}\n"

    # 第七步：添加统计分析
    if not df.empty:
        result += "=== 龙虎榜分析 ===\n"

        # 基本统计
        total_stocks = len(df)
        result += f"上榜股票总数: {total_stocks}只\n"

        # 涨跌统计
        if '涨跌幅' in df.columns:
            rising_stocks = len(df[df['涨跌幅'] > 0])
            falling_stocks = len(df[df['涨跌幅'] < 0])
            flat_stocks = len(df[df['涨跌幅'] == 0])

            result += f"上涨股票: {rising_stocks}只 ({rising_stocks/total_stocks*100:.1f}%)\n"
            result += f"下跌股票: {falling_stocks}只 ({falling_stocks/total_stocks*100:.1f}%)\n"
            result += f"平盘股票: {flat_stocks}只\n"

        # 资金流向统计
        if '龙虎榜净买额' in df.columns:
            net_inflow_stocks = len(df[df['龙虎榜净买额'] > 0])
            net_outflow_stocks = len(df[df['龙虎榜净买额'] < 0])
            total_net_buy = df['龙虎榜净买额'].sum() / 100000000

            result += f"净买入股票: {net_inflow_stocks}只\n"
            result += f"净卖出股票: {net_outflow_stocks}只\n"
            result += f"龙虎榜总净买额: {total_net_buy:.2f}亿元\n"

        # 上榜原因统计
        if '上榜原因' in df.columns:
            reason_counts = df['上榜原因'].value_counts().head(5)
            result += f"\n主要上榜原因:\n"
            for reason, count in reason_counts.items():
                result += f"  {reason}: {count}只\n"

        # 投资提示
        result += f"\n💡 投资提示:\n"
        result += f"- 龙虎榜反映大资金动向和市场关注度\n"
        result += f"- 净买额为正表示大资金看好，为负表示大资金减持\n"
        result += f"- 关注上榜原因，异常波动可能存在风险\n"
        result += f"- 建议结合基本面和技术面进行综合分析\n"

    # 第八步：添加数据说明
    result += f"\n数据统计: 共 {len(df)} 条龙虎榜记录"
    result += f"\n数据来源: 东方财富网龙虎榜"
    result += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return result


if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="运行股票数据 MCP HTTP 服务器")
    parser.add_argument("--port", type=int, default=8124, help="监听端口号")
    parser.add_argument("--host", type=str, default="localhost", help="监听主机地址")
    args = parser.parse_args()

    print(f"启动股票 MCP 服务器...")
    print(f"监听地址: http://{args.host}:{args.port}")
    print(f"支持的功能: 历史行情查询、分时数据查询、近期历史行情")
    
    # 启动服务器，使用流式 HTTP 传输
    uvicorn.run(mcp.streamable_http_app, host=args.host, port=args.port)
