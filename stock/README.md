# Stock MCP Server

一个基于 MCP (Model Context Protocol) 的股票金融数据服务，为 AI 大模型提供中国股市数据查询能力。

## 项目简介

本项目使用 `akshare` 库作为数据源，通过 MCP 协议为 AI 应用提供标准化的股票数据接口。支持历史行情查询、分时数据获取等核心功能，帮助构建可组合、安全和可扩展的 AI 金融工作流。

## 功能特性

### 核心功能

1. **历史行情查询** (`get_stock_history`)
   - 获取指定股票的历史交易数据
   - 支持日/周/月频率
   - 支持前复权/后复权
   - 返回：日期、开盘价、收盘价、最高价、最低价、成交量、成交额、涨跌幅等

2. **分时数据查询** (`get_stock_intraday`)
   - 获取股票分时交易数据
   - 默认60分钟间隔
   - 支持1/5/15/30/60分钟级别
   - 返回：时间、开盘价、收盘价、最高价、最低价、成交量、成交额、均价

### 扩展功能

3. **近期历史行情** (`get_recent_history`)
   - 快速获取近20天的历史行情数据
   - 便于快速了解股票近期走势
   - 包含简单的趋势分析和成交量对比

4. **股票基本信息** (`get_stock_info`)
   - 获取股票详细基本信息
   - 包含股票名称、代码、最新价格、总股本、流通股
   - 总市值、流通市值、所属行业、上市时间等

5. **筹码分布分析** (`get_stock_chip_distribution`)
   - 获取股票筹码分布数据（近90个交易日）
   - 包含获利比例、平均成本、成本分布区间
   - 90%/70%集中度分析、趋势变化分析

6. **股票代码查询** (`search_stock_code`)
   - 股票代码和名称双向查询
   - 支持精确匹配和模糊搜索
   - 自动识别查询类型（代码/名称）

### 市场分析功能

7. **股票热度排行** (`get_stock_hot_rank`)
   - 获取东方财富股票人气排行榜
   - 包含热度值、价格、涨跌幅等信息
   - 反映市场关注度和投资者情绪

8. **个股资金流向** (`get_individual_fund_flow`)
   - 支持即时和多日排行数据
   - 主力、超大单、大单资金流向分析
   - 帮助判断资金动向和市场趋势

9. **概念资金流向** (`get_concept_fund_flow`)
   - 概念板块资金流向排行
   - 包含概念指数、净流入、领涨股
   - 把握市场热点和投资主题

10. **行业资金流向** (`get_industry_fund_flow`)
    - 行业板块资金流向分析
    - 支持多时间周期排行数据
    - 反映产业投资趋势和轮动

11. **行业板块总览** (`get_industry_board_overview`)
    - 全市场行业板块综合表现
    - 涨跌分布、资金流向、成交活跃度
    - 提供市场全景分析和投资策略

12. **龙虎榜详情** (`get_dragon_tiger_list`)
    - 获取龙虎榜详情数据，反映大额交易情况
    - 支持指定日期范围查询，默认最近7天
    - 包含净买额、成交额占比、上榜原因等
    - 提供资金流向分析和投资风险提示

## 技术栈

- **数据源**: [akshare](https://github.com/akfamily/akshare) - 中国股市数据接口
- **MCP 框架**: [FastMCP](https://github.com/pydantic/fastmcp) - 快速构建 MCP 服务
- **Web 框架**: FastAPI + Uvicorn
- **数据处理**: pandas

## 项目结构

```
stock/
├── README.md                      # 项目说明文档
├── USAGE.md                       # 详细使用指南
├── stock_mcp_server.py           # 主服务文件
├── requirements.txt              # 依赖文件
├── test.py                       # 基础功能测试
├── test_mcp_client.py            # MCP 客户端测试 🧪
├── start.sh                      # 启动脚本 🚀
├── stop.sh                       # 停止脚本 🛑
├── demo.sh                       # 演示脚本
├── claude_desktop_config.json    # Claude Desktop 配置示例
├── stock_mcp.pid                 # 进程ID文件（运行时生成）
├── stock_mcp.log                 # 服务日志文件（运行时生成）
├── .augment/
│   └── rules/
│       └── rule.md               # 开发规则文档
└── docs/                         # 扩展文档目录
```

## 安装依赖

```bash
pip install akshare fastmcp uvicorn httpx pandas
```

## 使用方法

### 快速启动（推荐）

使用提供的启动脚本，自动处理依赖检查和服务管理：

```bash
# 前台运行（开发调试）
./start.sh

# 后台运行（生产环境）
./start.sh -d

# 自定义端口
./start.sh -p 8125

# 停止服务
./stop.sh

# 查看服务状态
./stop.sh -s
```

### 手动启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python stock_mcp_server.py --port 8124
```

服务将在 `http://localhost:8124` 启动。

详细使用说明请参考 [USAGE.md](USAGE.md)。

## MCP 客户端集成

### 配置 MCP 客户端

股票 MCP 服务启动后，可以通过 MCP 客户端连接使用。以下是常见的集成方式：

#### 1. Claude Desktop 集成

在 Claude Desktop 的配置文件中添加服务配置：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stock-data": {
      "command": "python",
      "args": ["/path/to/stock/stock_mcp_server.py", "--port", "8124"],
      "env": {}
    }
  }
}
```

#### 2. HTTP 客户端集成

对于支持 HTTP 传输的 MCP 客户端：

```json
{
  "mcpServers": {
    "stock-data": {
      "transport": "http",
      "url": "http://localhost:8124/mcp"
    }
  }
}
```

#### 3. 自定义客户端集成

使用 MCP SDK 连接到服务：

```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp.client.sse import SseServerParameters

async def connect_to_stock_mcp():
    # HTTP/SSE 连接方式
    server_params = SseServerParameters(
        url="http://localhost:8124"
    )

    async with ClientSession(server_params) as session:
        # 初始化连接
        await session.initialize()

        # 列出可用工具
        tools = await session.list_tools()
        print("可用工具:", [tool.name for tool in tools.tools])

        # 调用工具
        result = await session.call_tool(
            "get_stock_history",
            arguments={
                "symbol": "000001",
                "period": "daily",
                "start_date": "20241201",
                "end_date": "20241213"
            }
        )
        print("查询结果:", result.content)

# 运行客户端
asyncio.run(connect_to_stock_mcp())
```

### 可用的 MCP 工具

服务提供以下 MCP 工具函数，可通过客户端调用：

#### 1. `get_stock_history` - 历史行情查询

```json
{
  "name": "get_stock_history",
  "arguments": {
    "symbol": "000001",
    "period": "daily",
    "start_date": "20241201",
    "end_date": "20241213",
    "adjust": ""
  }
}
```

#### 2. `get_stock_intraday` - 分时数据查询

```json
{
  "name": "get_stock_intraday",
  "arguments": {
    "symbol": "000001",
    "date": "20241213",
    "period": "60",
    "adjust": ""
  }
}
```

#### 3. `get_recent_history` - 近期历史行情

```json
{
  "name": "get_recent_history",
  "arguments": {
    "symbol": "000001",
    "adjust": ""
  }
}
```

#### 4. `get_stock_info` - 股票基本信息

```json
{
  "name": "get_stock_info",
  "arguments": {
    "symbol": "000001"
  }
}
```

#### 5. `get_stock_chip_distribution` - 筹码分布分析

```json
{
  "name": "get_stock_chip_distribution",
  "arguments": {
    "symbol": "000001",
    "adjust": ""
  }
}
```

#### 6. `search_stock_code` - 股票代码查询

```json
{
  "name": "search_stock_code",
  "arguments": {
    "query": "000001"
  }
}
```

#### 7. `get_stock_hot_rank` - 股票热度排行

```json
{
  "name": "get_stock_hot_rank",
  "arguments": {}
}
```

#### 8. `get_individual_fund_flow` - 个股资金流向

```json
{
  "name": "get_individual_fund_flow",
  "arguments": {
    "symbol": "即时"
  }
}
```

#### 9. `get_concept_fund_flow` - 概念资金流向

```json
{
  "name": "get_concept_fund_flow",
  "arguments": {
    "symbol": "即时"
  }
}
```

#### 10. `get_industry_fund_flow` - 行业资金流向

```json
{
  "name": "get_industry_fund_flow",
  "arguments": {
    "symbol": "即时"
  }
}
```

#### 11. `get_industry_board_overview` - 行业板块总览

```json
{
  "name": "get_industry_board_overview",
  "arguments": {}
}
```

#### 12. `get_dragon_tiger_list` - 龙虎榜详情

```json
{
  "name": "get_dragon_tiger_list",
  "arguments": {
    "start_date": "20240401",
    "end_date": "20240407"
  }
}
```

### AI 助手使用示例

当 MCP 客户端（如 Claude）连接到服务后，可以直接使用自然语言查询：

```
用户: 帮我查询平安银行最近5天的股价走势

AI: 我来为您查询平安银行(000001)最近的股价走势。

[调用 get_recent_history 工具]

根据查询结果，平安银行最近5天的走势如下：
- 最新收盘价：10.45元，下跌1.23%
- 近期呈现下降趋势...
```

```
用户: 查询贵州茅台今天的60分钟K线数据

AI: 我来查询贵州茅台(600519)今天的60分钟K线数据。

[调用 get_stock_intraday 工具]

贵州茅台今日60分钟K线数据：
- 开盘价：1650.00元
- 当前价：1645.50元
- 成交量：较为活跃...
```

```
用户: 帮我查询万科A的基本信息

AI: 我来为您查询万科A(000002)的基本信息。

[调用 get_stock_info 工具]

万科A基本信息：
- 股票简称：万科A
- 最新价格：7.05元
- 总股本：11,930,709,471股
- 流通市值：68,504,397,848元
- 所属行业：房地产开发
- 上市时间：1991-01-29
```

```
用户: 帮我分析一下平安银行的筹码分布情况

AI: 我来为您分析平安银行(000001)的筹码分布情况。

[调用 get_stock_chip_distribution 工具]

平安银行筹码分布分析：
- 最新获利比例：7.44%（大部分投资者处于亏损状态）
- 平均成本：11.25元
- 90%成本分布：9.16元 - 12.56元（区间3.40元）
- 90%集中度：0.1733（筹码相对集中）
- 筹码主要集中在11元附近，支撑较强
```

```
用户: 帮我查询一下股票代码000001对应的是什么股票

AI: 我来为您查询股票代码000001对应的股票信息。

[调用 search_stock_code 工具]

查询结果：
- 代码：000001
- 名称：平安银行
- 市场：深圳证券交易所
- 最新价：10.50元
- 涨跌幅：+1.23%
```

```
用户: 我想找"平安"相关的股票有哪些

AI: 我来为您搜索包含"平安"的相关股票。

[调用 search_stock_code 工具]

找到 3 只相关股票：
1. 000001 平安银行 (深)
2. 601318 中国平安 (沪)
3. 002142 宁波银行 (深)

您可以进一步查询具体股票的详细信息。
```

```
用户: 帮我看看当前市场热点是什么

AI: 我来为您分析当前市场热点情况。

[调用 get_stock_hot_rank 工具]
[调用 get_concept_fund_flow 工具]

当前市场热点分析：

📈 热门股票TOP5：
1. 000001 平安银行 (人气值: 12345)
2. 600519 贵州茅台 (人气值: 11234)
...

🔥 热门概念板块：
1. 人工智能: 净流入 12.34亿元 (+3.45%)
2. 新能源汽车: 净流入 8.76亿元 (+2.15%)
...

💡 投资建议：当前市场关注AI和新能源概念，建议关注相关龙头股
```

```
用户: 分析一下今天的资金流向情况

AI: 我来为您分析今天的市场资金流向情况。

[调用 get_individual_fund_flow 工具]
[调用 get_industry_fund_flow 工具]
[调用 get_industry_board_overview 工具]

今日资金流向分析：

💰 个股资金流向：
- 主力净流入股票: 1234只
- 主力净流出股票: 2345只
- 整体资金流向: 净流出 45.67亿元

🏭 行业资金流向：
- 净流入行业: 电子信息 (+12.34亿)
- 净流出行业: 房地产 (-8.76亿)

📊 市场情绪: 偏空，建议谨慎操作
```

```
用户: 帮我看看最近有哪些股票上了龙虎榜

AI: 我来为您查询最近的龙虎榜情况。

[调用 get_dragon_tiger_list 工具]

最近龙虎榜情况：

📅 2024-04-07 (15只股票上榜)
1. 000001 平安银行: +3.45%📈 净买额 +1.23亿元 (日涨幅偏离值达7%)
2. 600519 贵州茅台: -2.15%📉 净买额 -0.87亿元 (日跌幅偏离值达7%)
...

📊 龙虎榜分析：
- 上榜股票总数: 45只
- 上涨股票: 28只 (62.2%)
- 龙虎榜总净买额: +12.34亿元

💡 投资提示：大资金整体呈现净买入状态，市场情绪相对乐观
```

### API 接口示例

#### 1. 历史行情查询

```python
# 获取平安银行(000001)近一个月日线数据
get_stock_history(
    symbol="000001",
    period="daily",
    start_date="20241201",
    end_date="20241231"
)
```

#### 2. 分时数据查询

```python
# 获取平安银行(000001)今日60分钟K线数据
get_stock_intraday(
    symbol="000001",
    date="20241213",
    period="60"
)
```

#### 3. 近期历史行情

```python
# 获取平安银行(000001)近20天行情
get_recent_history(symbol="000001")
```

#### 4. 股票基本信息

```python
# 获取平安银行(000001)基本信息
get_stock_info(symbol="000001")
```

#### 5. 筹码分布分析

```python
# 获取平安银行(000001)筹码分布
get_stock_chip_distribution(symbol="000001", adjust="")
```

#### 6. 股票代码查询

```python
# 根据股票代码查询名称
search_stock_code(query="000001")

# 根据股票名称查询代码
search_stock_code(query="平安银行")

# 模糊查询
search_stock_code(query="平安")
```

#### 7. 市场分析功能

```python
# 股票热度排行榜
get_stock_hot_rank()

# 个股资金流向（即时/排行）
get_individual_fund_flow(symbol="即时")
get_individual_fund_flow(symbol="3日排行")

# 概念资金流向
get_concept_fund_flow(symbol="即时")

# 行业资金流向
get_industry_fund_flow(symbol="即时")

# 行业板块总览
get_industry_board_overview()

# 龙虎榜详情（最近7天）
get_dragon_tiger_list()

# 龙虎榜详情（指定日期范围）
get_dragon_tiger_list(start_date="20240401", end_date="20240407")
```

## 数据格式说明

### 历史行情数据字段

| 字段名   | 类型    | 说明           |
|----------|---------|----------------|
| 日期     | string  | 交易日期       |
| 股票代码 | string  | 股票代码       |
| 开盘     | float   | 开盘价(元)     |
| 收盘     | float   | 收盘价(元)     |
| 最高     | float   | 最高价(元)     |
| 最低     | float   | 最低价(元)     |
| 成交量   | int     | 成交量(手)     |
| 成交额   | float   | 成交额(元)     |
| 振幅     | float   | 振幅(%)        |
| 涨跌幅   | float   | 涨跌幅(%)      |
| 涨跌额   | float   | 涨跌额(元)     |
| 换手率   | float   | 换手率(%)      |

### 分时数据字段

| 字段名 | 类型    | 说明           |
|--------|---------|----------------|
| 时间   | string  | 交易时间       |
| 开盘   | float   | 开盘价(元)     |
| 收盘   | float   | 收盘价(元)     |
| 最高   | float   | 最高价(元)     |
| 最低   | float   | 最低价(元)     |
| 成交量 | float   | 成交量(手)     |
| 成交额 | float   | 成交额(元)     |
| 均价   | float   | 均价(元)       |

## 股票代码格式

支持中国A股股票代码，格式为6位数字：
- 上海证券交易所：600xxx, 601xxx, 603xxx, 688xxx
- 深圳证券交易所：000xxx, 001xxx, 002xxx, 003xxx, 300xxx

示例：
- `000001` - 平安银行
- `000002` - 万科A
- `600036` - 招商银行
- `600519` - 贵州茅台

### 测试 MCP 连接

#### 使用 curl 测试服务

```bash
# 启动服务
./start.sh -d

# 测试服务是否正常运行
curl -X GET http://localhost:8124/health

# 测试 MCP 工具调用（需要 MCP 客户端）
curl -X POST http://localhost:8124/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_recent_history",
      "arguments": {
        "symbol": "000001"
      }
    }
  }'
```

#### 使用 Python MCP 客户端测试

```python
# test_mcp_client.py
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import SseServerParameters

async def test_stock_mcp():
    """测试股票 MCP 服务"""
    server_params = SseServerParameters(
        url="http://localhost:8124"
    )

    try:
        async with ClientSession(server_params) as session:
            # 初始化
            await session.initialize()
            print("✅ MCP 连接成功")

            # 列出工具
            tools_result = await session.list_tools()
            print(f"📋 可用工具: {[t.name for t in tools_result.tools]}")

            # 测试近期历史行情
            print("\n🔍 测试查询平安银行近期行情...")
            result = await session.call_tool(
                "get_recent_history",
                arguments={"symbol": "000001"}
            )
            print("📊 查询结果:")
            print(result.content[0].text[:500] + "...")

    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_stock_mcp())
```

### 生产环境部署

#### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x start.sh stop.sh

EXPOSE 8124
CMD ["python", "stock_mcp_server.py", "--host", "0.0.0.0", "--port", "8124"]
```

构建和运行：

```bash
# 构建镜像
docker build -t stock-mcp .

# 运行容器
docker run -d -p 8124:8124 --name stock-mcp-server stock-mcp

# 查看日志
docker logs stock-mcp-server
```

#### 反向代理配置

使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8124;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## 注意事项

1. **数据延迟**: 历史数据按日频率更新，当日收盘价请在收盘后获取
2. **分时数据限制**: 1分钟数据只返回近5个交易日数据且不复权
3. **请求频率**: 建议控制请求频率，避免对数据源造成压力
4. **交易时间**: 分时数据仅在交易时间内有效（9:30-11:30, 13:00-15:00）
5. **MCP 兼容性**: 确保客户端支持 MCP 协议版本
6. **网络安全**: 生产环境建议配置 HTTPS 和访问控制

## 开发计划

- [x] 基础项目结构
- [x] 实现历史行情查询接口
- [x] 实现分时数据查询接口
- [x] 实现近期历史行情接口
- [x] 股票基本信息接口
- [x] 筹码分布分析接口
- [x] 股票代码查询接口
- [x] 股票热度排行接口
- [x] 个股资金流向接口
- [x] 概念资金流向接口
- [x] 行业资金流向接口
- [x] 行业板块总览接口
- [x] 龙虎榜详情接口
- [x] 添加错误处理和数据验证
- [x] 添加基础测试
- [x] MCP 客户端集成说明
- [x] 启动停止脚本
- [ ] 性能优化和缓存机制
- [ ] 完整单元测试覆盖

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 许可证

MIT License

