---
type: "manual"
---

# Stock MCP Server 开发规则

## 1. 技术栈规范

### 1.1 开发语言
- **主语言**: Python 3.8+
- **类型提示**: 必须使用 Python 类型提示 (Type Hints)
- **代码风格**: 遵循 PEP 8 规范

### 1.2 开发框架
- **MCP 框架**: 使用 MCP HTTP 协议
- **具体实现**: 基于 `FastMCP` 框架构建服务
- **Web 服务**: 使用 `uvicorn` 作为 ASGI 服务器
- **HTTP 客户端**: 使用 `httpx` 进行异步 HTTP 请求

### 1.3 核心依赖
```python
# 必需依赖
akshare          # 股票数据源
fastmcp          # MCP 框架
uvicorn          # ASGI 服务器
httpx            # HTTP 客户端
pandas           # 数据处理
```

## 2. 项目结构规范

### 2.1 文件组织
```
stock/
├── README.md                 # 项目说明文档（必需）
├── stock_mcp_server.py      # 主服务文件
├── requirements.txt         # 依赖文件
├── test.py                  # 测试文件
├── .augment/
│   └── rules/
│       └── rule.md          # 开发规则文档
└── docs/                    # 扩展文档目录
```

### 2.2 文档要求
- **README.md**: 必须包含完整的项目说明、API 文档、使用示例
- **代码注释**: 每个函数、类、重要逻辑都必须有详细注释
- **类型提示**: 所有函数参数和返回值都必须有类型注释

## 3. 代码规范

### 3.1 注释规范

#### 3.1.1 函数注释格式
```python
async def get_stock_history(
    symbol: str,
    period: str = "daily",
    start_date: str = "",
    end_date: str = "",
    adjust: str = ""
) -> str:
    """获取股票历史行情数据

    通过 akshare 接口获取指定股票的历史交易数据，支持不同周期和复权方式。

    Args:
        symbol (str): 股票代码，6位数字格式，如 "000001"
        period (str, optional): 数据周期. Defaults to "daily".
            - "daily": 日线数据
            - "weekly": 周线数据
            - "monthly": 月线数据
        start_date (str, optional): 开始日期，格式 "YYYYMMDD". Defaults to "".
        end_date (str, optional): 结束日期，格式 "YYYYMMDD". Defaults to "".
        adjust (str, optional): 复权方式. Defaults to "".
            - "": 不复权
            - "qfq": 前复权
            - "hfq": 后复权

    Returns:
        str: 格式化的历史行情数据字符串，包含日期、价格、成交量等信息

    Raises:
        Exception: 当股票代码无效或网络请求失败时抛出异常

    Example:
        >>> await get_stock_history("000001", "daily", "20241201", "20241231")
        "日期: 2024-12-01, 开盘: 10.50, 收盘: 10.80, ..."
    """
```

#### 3.1.2 类注释格式
```python
class StockDataProcessor:
    """股票数据处理器

    负责处理从 akshare 获取的原始股票数据，进行格式化、验证和转换。

    Attributes:
        timeout (float): 请求超时时间，默认 30 秒
        retry_count (int): 重试次数，默认 3 次

    Example:
        >>> processor = StockDataProcessor(timeout=60.0)
        >>> data = await processor.process_history_data(raw_data)
    """
```

#### 3.1.3 行内注释规范
```python
# 设置请求头，包含用户代理和接受类型
headers = {
    "User-Agent": "stock-mcp-server/1.0",  # 标识客户端
    "Accept": "application/json"           # 指定响应格式
}

# 异步获取股票数据，设置30秒超时
async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers, timeout=30.0)
```

### 3.2 错误处理规范

#### 3.2.1 异常处理模式
```python
async def safe_api_call(url: str) -> dict | None:
    """安全的 API 调用，包含完整的错误处理

    Args:
        url (str): 请求的 URL 地址

    Returns:
        dict | None: 成功时返回数据字典，失败时返回 None
    """
    try:
        # 发起 HTTP 请求
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()  # 检查 HTTP 状态码
            return response.json()

    except httpx.TimeoutException:
        # 处理超时异常
        print(f"请求超时: {url}")
        return None

    except httpx.HTTPStatusError as e:
        # 处理 HTTP 错误状态码
        print(f"HTTP 错误 {e.response.status_code}: {url}")
        return None

    except Exception as e:
        # 处理其他未预期的异常
        print(f"未知错误: {str(e)}")
        return None
```

### 3.3 MCP 工具注册规范

#### 3.3.1 工具装饰器使用
```python
@mcp.tool()
async def get_stock_history(symbol: str, period: str = "daily") -> str:
    """获取股票历史行情数据

    MCP 工具函数，为 AI 模型提供股票历史数据查询能力。

    Args:
        symbol (str): 股票代码，如 "000001"
        period (str): 数据周期，默认 "daily"

    Returns:
        str: 格式化的历史行情数据
    """
    # 验证股票代码格式
    if not symbol or len(symbol) != 6 or not symbol.isdigit():
        return "错误: 股票代码格式无效，请输入6位数字代码"

    # 调用数据获取逻辑
    try:
        data = await fetch_stock_history(symbol, period)
        return format_history_data(data)
    except Exception as e:
        return f"获取数据失败: {str(e)}"
```

## 4. 开发流程规范

### 4.1 开发步骤
1. **需求分析**: 明确功能需求和 API 设计
2. **接口设计**: 定义 MCP 工具函数签名和文档
3. **核心实现**: 实现数据获取和处理逻辑
4. **错误处理**: 添加完整的异常处理机制
5. **测试验证**: 编写测试用例验证功能
6. **文档更新**: 更新 README 和代码注释

### 4.2 代码提交规范
- 每个功能模块独立提交
- 提交信息格式: `feat: 添加股票历史行情查询功能`
- 确保代码通过基本测试后再提交

### 4.3 测试要求
- 每个 MCP 工具函数都需要有对应的测试用例
- 测试覆盖正常情况和异常情况
- 使用真实的股票代码进行集成测试

## 5. 性能和安全规范

### 5.1 性能要求
- API 响应时间控制在 5 秒以内
- 合理使用缓存机制避免重复请求
- 异步处理提高并发能力

### 5.2 安全要求
- 输入参数验证和清理
- 避免 SQL 注入和其他安全漏洞
- 合理的请求频率限制

## 6. AI 友好性规范

### 6.1 函数命名
- 使用清晰、描述性的函数名
- 遵循 `动词_名词` 的命名模式
- 例如: `get_stock_history`, `format_price_data`

### 6.2 参数设计
- 参数名称要直观易懂
- 提供合理的默认值
- 使用类型提示明确参数类型

### 6.3 返回值格式
- 统一使用字符串格式返回结果
- 包含清晰的数据结构说明
- 错误信息要具体和可操作

---

**注意**: 本规则文档会随着项目发展持续更新，所有开发者都应遵循最新版本的规范。