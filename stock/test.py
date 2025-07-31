"""股票 MCP 服务器测试脚本

测试股票 MCP 服务器的各项功能，包括：
1. 历史行情查询
2. 分时数据查询
3. 近期历史行情
4. 股票基本信息

使用方法:
1. 确保已安装依赖: pip install -r requirements.txt
2. 运行测试: python test.py
"""

import asyncio
import time
from datetime import datetime

# 导入我们的 MCP 服务器模块
from stock_mcp_server import (
    get_stock_history,
    get_stock_intraday,
    get_recent_history,
    get_stock_info,
    get_stock_chip_distribution,
    search_stock_code,
    get_stock_hot_rank,
    get_individual_fund_flow,
    get_concept_fund_flow,
    get_industry_fund_flow,
    get_industry_board_overview,
    get_dragon_tiger_list,
    validate_stock_symbol,
    format_date_string,
    get_recent_date_range
)


async def test_validate_stock_symbol():
    """测试股票代码验证功能"""
    print("=== 测试股票代码验证 ===")

    # 测试有效代码
    valid_codes = ["000001", "600519", "300750", "688981"]
    for code in valid_codes:
        result = validate_stock_symbol(code)
        print(f"代码 {code}: {'✓ 有效' if result else '✗ 无效'}")

    # 测试无效代码
    invalid_codes = ["12345", "0000001", "abc123", "", "60051"]
    for code in invalid_codes:
        result = validate_stock_symbol(code)
        print(f"代码 {code}: {'✓ 有效' if result else '✗ 无效'}")

    print()


async def test_date_functions():
    """测试日期处理功能"""
    print("=== 测试日期处理功能 ===")

    # 测试日期格式化
    test_dates = ["20241213", "2024-12-13", "2024/12/13", "2024.12.13"]
    for date in test_dates:
        try:
            formatted = format_date_string(date)
            print(f"日期 {date} -> {formatted}")
        except ValueError as e:
            print(f"日期 {date} -> 错误: {e}")

    # 测试近期日期范围
    start, end = get_recent_date_range()
    print(f"近期日期范围: {start} 到 {end}")
    print()


async def test_stock_history():
    """测试历史行情查询功能"""
    print("=== 测试历史行情查询 ===")

    # 测试基本查询
    print("1. 测试基本历史行情查询（平安银行近5天）...")
    start_time = time.time()

    # 计算近5天的日期范围
    today = datetime.now()
    end_date = today.strftime("%Y%m%d")
    start_date = (today - timedelta(days=5)).strftime("%Y%m%d")

    result = await get_stock_history("000001", "daily", start_date, end_date)
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()

    # 测试错误情况
    print("2. 测试错误股票代码...")
    error_result = await get_stock_history("999999")
    print("错误结果:", error_result[:200])
    print()


async def test_stock_intraday():
    """测试分时数据查询功能"""
    print("=== 测试分时数据查询 ===")

    print("1. 测试60分钟分时数据（平安银行今日）...")
    start_time = time.time()

    today = datetime.now().strftime("%Y%m%d")
    result = await get_stock_intraday("000001", today, "60")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()


async def test_recent_history():
    """测试近期历史行情功能"""
    print("=== 测试近期历史行情 ===")

    print("1. 测试近期历史行情（贵州茅台）...")
    start_time = time.time()

    result = await get_recent_history("600519")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:800] + "..." if len(result) > 800 else result)
    print()


async def test_stock_info():
    """测试股票基本信息功能"""
    print("=== 测试股票基本信息 ===")

    print("1. 测试股票基本信息（平安银行）...")
    start_time = time.time()

    result = await get_stock_info("000001")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result)
    print()

    print("2. 测试股票基本信息（万科A）...")
    start_time = time.time()

    result = await get_stock_info("000002")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()


async def test_chip_distribution():
    """测试筹码分布功能"""
    print("=== 测试筹码分布 ===")

    print("1. 测试筹码分布（平安银行）...")
    start_time = time.time()

    result = await get_stock_chip_distribution("000001")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:800] + "..." if len(result) > 800 else result)
    print()


async def test_search_stock_code():
    """测试股票代码查询功能"""
    print("=== 测试股票代码查询 ===")

    print("1. 测试根据代码查询名称（平安银行）...")
    start_time = time.time()

    result = await search_stock_code("000001")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result)
    print()

    print("2. 测试根据名称查询代码（贵州茅台）...")
    start_time = time.time()

    result = await search_stock_code("贵州茅台")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result)
    print()

    print("3. 测试模糊查询（平安）...")
    start_time = time.time()

    result = await search_stock_code("平安")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()


async def test_market_analysis():
    """测试市场分析功能"""
    print("=== 测试市场分析功能 ===")

    print("1. 测试股票热度排行...")
    start_time = time.time()

    result = await get_stock_hot_rank()
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()

    print("2. 测试个股资金流（即时）...")
    start_time = time.time()

    result = await get_individual_fund_flow("即时")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()

    print("3. 测试概念资金流（即时）...")
    start_time = time.time()

    result = await get_concept_fund_flow("即时")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()

    print("4. 测试行业资金流（即时）...")
    start_time = time.time()

    result = await get_industry_fund_flow("即时")
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()

    print("5. 测试行业板块总览...")
    start_time = time.time()

    result = await get_industry_board_overview()
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()


async def test_dragon_tiger_list():
    """测试龙虎榜功能"""
    print("=== 测试龙虎榜功能 ===")

    print("1. 测试龙虎榜详情（最近7天）...")
    start_time = time.time()

    result = await get_dragon_tiger_list()
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:800] + "..." if len(result) > 800 else result)
    print()

    print("2. 测试龙虎榜详情（指定日期）...")
    start_time = time.time()

    # 查询最近3天的数据
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")

    result = await get_dragon_tiger_list(start_date, end_date)
    elapsed = time.time() - start_time

    print(f"查询耗时: {elapsed:.2f}秒")
    print("查询结果:")
    print(result[:600] + "..." if len(result) > 600 else result)
    print()


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始股票 MCP 服务器功能测试")
    print("=" * 50)

    total_start = time.time()

    # 运行各项测试
    await test_validate_stock_symbol()
    await test_date_functions()
    await test_stock_history()
    await test_stock_intraday()
    await test_recent_history()
    await test_stock_info()
    await test_chip_distribution()
    await test_search_stock_code()
    await test_market_analysis()
    await test_dragon_tiger_list()

    total_elapsed = time.time() - total_start

    print("=" * 50)
    print(f"✅ 所有测试完成，总耗时: {total_elapsed:.2f}秒")
    print("\n注意事项:")
    print("1. 某些测试可能因为网络或数据源问题而失败")
    print("2. 分时数据在非交易时间可能返回空数据")
    print("3. 股票基本信息查询需要有效的股票代码")
    print("4. 筹码分布数据来源于东方财富，提供近90个交易日数据")
    print("5. 股票代码查询支持代码和名称双向查询")
    print("6. 市场分析功能包含热度、资金流、板块等多维度数据")
    print("7. 龙虎榜数据反映大资金动向和异常波动情况")
    print("8. 实际使用时建议添加重试机制")


if __name__ == "__main__":
    # 导入 timedelta（用于日期计算）
    from datetime import timedelta

    # 运行异步测试
    asyncio.run(run_all_tests())

    # 如果需要单独测试 akshare 接口，可以取消下面的注释
    # import akshare as ak
    # stock_individual_info_em_df = ak.stock_individual_info_em(symbol="000001")
    # print(stock_individual_info_em_df)