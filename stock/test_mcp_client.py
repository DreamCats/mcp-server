"""MCP 客户端测试脚本

测试股票 MCP 服务的客户端连接和工具调用功能。

使用方法:
1. 启动股票 MCP 服务: ./start.sh -d
2. 运行测试脚本: python test_mcp_client.py

注意: 需要安装 MCP 客户端库
pip install mcp
"""

import asyncio
import json
import time
from typing import Optional

try:
    from mcp.client.session import ClientSession
    from mcp.client.sse import SseServerParameters
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️  MCP 客户端库未安装，请运行: pip install mcp")
    MCP_AVAILABLE = False

# 测试配置
SERVER_URL = "http://localhost:8124"
TEST_SYMBOLS = ["000001", "600519", "000002"]  # 平安银行、贵州茅台、万科A


class StockMCPTester:
    """股票 MCP 服务测试器"""
    
    def __init__(self, server_url: str = SERVER_URL):
        """初始化测试器
        
        Args:
            server_url (str): MCP 服务器地址
        """
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        
    async def connect(self) -> bool:
        """连接到 MCP 服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            print(f"🔗 正在连接到 MCP 服务器: {self.server_url}")
            
            server_params = SseServerParameters(url=self.server_url)
            self.session = ClientSession(server_params)
            
            # 初始化连接
            await self.session.initialize()
            print("✅ MCP 连接成功")
            return True
            
        except Exception as e:
            print(f"❌ MCP 连接失败: {e}")
            print("💡 请确保股票 MCP 服务已启动: ./start.sh -d")
            return False
    
    async def list_tools(self):
        """列出可用的 MCP 工具"""
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return
        
        try:
            print("\n📋 获取可用工具列表...")
            tools_result = await self.session.list_tools()
            
            print(f"✅ 发现 {len(tools_result.tools)} 个工具:")
            for tool in tools_result.tools:
                print(f"  📦 {tool.name}: {tool.description}")
                
        except Exception as e:
            print(f"❌ 获取工具列表失败: {e}")
    
    async def test_recent_history(self, symbol: str = "000001"):
        """测试近期历史行情查询
        
        Args:
            symbol (str): 股票代码
        """
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return
        
        try:
            print(f"\n🔍 测试近期历史行情查询 - {symbol}")
            start_time = time.time()
            
            result = await self.session.call_tool(
                "get_recent_history",
                arguments={"symbol": symbol}
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")
            print("📊 查询结果:")
            
            # 显示结果的前500个字符
            content = result.content[0].text if result.content else "无数据"
            print(content[:500] + ("..." if len(content) > 500 else ""))
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    async def test_stock_history(self, symbol: str = "600519"):
        """测试历史行情查询
        
        Args:
            symbol (str): 股票代码
        """
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return
        
        try:
            print(f"\n📈 测试历史行情查询 - {symbol}")
            start_time = time.time()
            
            # 查询最近10天的数据
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
            
            result = await self.session.call_tool(
                "get_stock_history",
                arguments={
                    "symbol": symbol,
                    "period": "daily",
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")
            print("📊 查询结果:")
            
            content = result.content[0].text if result.content else "无数据"
            print(content[:500] + ("..." if len(content) > 500 else ""))
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    async def test_intraday_data(self, symbol: str = "000002"):
        """测试分时数据查询
        
        Args:
            symbol (str): 股票代码
        """
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return
        
        try:
            print(f"\n⏰ 测试分时数据查询 - {symbol}")
            start_time = time.time()
            
            # 查询今天的60分钟数据
            today = datetime.now().strftime("%Y%m%d")
            
            result = await self.session.call_tool(
                "get_stock_intraday",
                arguments={
                    "symbol": symbol,
                    "date": today,
                    "period": "60"
                }
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")
            print("📊 查询结果:")
            
            content = result.content[0].text if result.content else "无数据"
            print(content[:500] + ("..." if len(content) > 500 else ""))
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")

    async def test_stock_info(self, symbol: str = "000001"):
        """测试股票基本信息功能

        Args:
            symbol (str): 股票代码
        """
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return

        try:
            print(f"\n📋 测试股票基本信息 - {symbol}")
            start_time = time.time()

            result = await self.session.call_tool(
                "get_stock_info",
                arguments={"symbol": symbol}
            )

            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")
            print("📊 查询结果:")

            content = result.content[0].text if result.content else "无数据"
            print(content)

        except Exception as e:
            print(f"❌ 查询失败: {e}")

    async def test_chip_distribution(self, symbol: str = "000001"):
        """测试筹码分布功能

        Args:
            symbol (str): 股票代码
        """
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return

        try:
            print(f"\n📊 测试筹码分布 - {symbol}")
            start_time = time.time()

            result = await self.session.call_tool(
                "get_stock_chip_distribution",
                arguments={"symbol": symbol}
            )

            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")
            print("📊 查询结果:")

            content = result.content[0].text if result.content else "无数据"
            print(content[:800] + ("..." if len(content) > 800 else ""))

        except Exception as e:
            print(f"❌ 查询失败: {e}")

    async def test_search_stock_code(self, query: str = "000001"):
        """测试股票代码查询功能

        Args:
            query (str): 查询内容（代码或名称）
        """
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return

        try:
            print(f"\n🔍 测试股票代码查询 - '{query}'")
            start_time = time.time()

            result = await self.session.call_tool(
                "search_stock_code",
                arguments={"query": query}
            )

            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")
            print("📊 查询结果:")

            content = result.content[0].text if result.content else "无数据"
            print(content)

        except Exception as e:
            print(f"❌ 查询失败: {e}")

    async def test_market_analysis(self):
        """测试市场分析功能"""
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return

        # 测试股票热度
        try:
            print(f"\n🔥 测试股票热度排行")
            start_time = time.time()

            result = await self.session.call_tool("get_stock_hot_rank", arguments={})
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")

            content = result.content[0].text if result.content else "无数据"
            print("📊 查询结果:")
            print(content[:400] + ("..." if len(content) > 400 else ""))

        except Exception as e:
            print(f"❌ 股票热度查询失败: {e}")

        # 测试个股资金流
        try:
            print(f"\n💰 测试个股资金流（即时）")
            start_time = time.time()

            result = await self.session.call_tool(
                "get_individual_fund_flow",
                arguments={"symbol": "即时"}
            )
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")

            content = result.content[0].text if result.content else "无数据"
            print("📊 查询结果:")
            print(content[:400] + ("..." if len(content) > 400 else ""))

        except Exception as e:
            print(f"❌ 个股资金流查询失败: {e}")

        # 测试行业板块总览
        try:
            print(f"\n🏭 测试行业板块总览")
            start_time = time.time()

            result = await self.session.call_tool("get_industry_board_overview", arguments={})
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")

            content = result.content[0].text if result.content else "无数据"
            print("📊 查询结果:")
            print(content[:400] + ("..." if len(content) > 400 else ""))

        except Exception as e:
            print(f"❌ 行业板块总览查询失败: {e}")

    async def test_dragon_tiger_list(self):
        """测试龙虎榜功能"""
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return

        try:
            print(f"\n🐉 测试龙虎榜详情（最近7天）")
            start_time = time.time()

            result = await self.session.call_tool("get_dragon_tiger_list", arguments={})
            elapsed = time.time() - start_time
            print(f"⏱️  查询耗时: {elapsed:.2f}秒")

            content = result.content[0].text if result.content else "无数据"
            print("📊 查询结果:")
            print(content[:500] + ("..." if len(content) > 500 else ""))

        except Exception as e:
            print(f"❌ 龙虎榜查询失败: {e}")

    async def test_error_handling(self):
        """测试错误处理"""
        if not self.session:
            print("❌ 未连接到 MCP 服务器")
            return
        
        print("\n🧪 测试错误处理...")
        
        # 测试无效股票代码
        try:
            print("  测试无效股票代码...")
            result = await self.session.call_tool(
                "get_recent_history",
                arguments={"symbol": "999999"}
            )
            content = result.content[0].text if result.content else "无响应"
            print(f"  结果: {content[:100]}...")
            
        except Exception as e:
            print(f"  异常: {e}")
        
        # 测试无效参数
        try:
            print("  测试无效参数...")
            result = await self.session.call_tool(
                "get_stock_history",
                arguments={
                    "symbol": "000001",
                    "period": "invalid_period"
                }
            )
            content = result.content[0].text if result.content else "无响应"
            print(f"  结果: {content[:100]}...")
            
        except Exception as e:
            print(f"  异常: {e}")
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            print("🔌 MCP 连接已关闭")


async def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始股票 MCP 客户端测试")
    print("=" * 50)
    
    if not MCP_AVAILABLE:
        return
    
    tester = StockMCPTester()
    
    try:
        # 连接测试
        if not await tester.connect():
            return
        
        # 工具列表测试
        await tester.list_tools()
        
        # 功能测试
        await tester.test_recent_history("000001")  # 平安银行
        await tester.test_stock_history("600519")   # 贵州茅台
        await tester.test_intraday_data("000002")   # 万科A
        await tester.test_stock_info("000001")      # 平安银行基本信息
        await tester.test_chip_distribution("000001")  # 平安银行筹码分布
        await tester.test_search_stock_code("000001")   # 股票代码查询
        await tester.test_search_stock_code("平安银行")  # 股票名称查询
        await tester.test_market_analysis()            # 市场分析功能
        await tester.test_dragon_tiger_list()          # 龙虎榜功能

        # 错误处理测试
        await tester.test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成")
        print("\n💡 提示:")
        print("- 如果某些查询返回空数据，可能是非交易时间或网络问题")
        print("- 分时数据在非交易时间可能无数据")
        print("- 可以修改 TEST_SYMBOLS 测试其他股票")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        
    finally:
        await tester.close()


if __name__ == "__main__":
    # 导入 datetime（用于日期计算）
    from datetime import datetime, timedelta
    
    # 运行测试
    asyncio.run(run_comprehensive_test())
