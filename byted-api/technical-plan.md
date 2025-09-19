# byted-api MCP 技术规划文档

## 1. 项目概述

### 1.1 项目背景
构建基于 MCP (Model Context Protocol) 的服务发现工具，集成字节跳动内部服务注册中心，提供 JWT 认证和 PSM (Product, Subsys, Module) 服务查询功能。

### 1.2 核心功能
- JWT 令牌获取与认证
- 双区域并发 PSM 服务查询
- MCP 标准化接口封装
- 异步 HTTP 请求处理

## 2. 技术架构

### 2.1 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  MCP Server     │    │  External APIs  │
│                 │────│                 │────│                 │
│  - Claude       │    │  - FastMCP      │    │  - Auth Service │
│  - Other Tools  │    │  - Tools        │    │  - Neptune      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ├─ JWT Auth Module
                              ├─ PSM Query Module
                              ├─ Concurrent Manager
                              └─ Error Handler
```

### 2.2 核心模块设计

#### 2.2.1 认证模块 (Auth Module)
```python
class JWTAuthManager:
    """JWT 令牌管理器"""

    def __init__(self, cookie_value: str):
        self.cookie_value = cookie_value
        self.jwt_token = None
        self.expires_at = None

    async def get_jwt_token(self) -> str:
        """获取 JWT 令牌"""
        # 实现令牌获取逻辑
        pass

    def is_token_valid(self) -> bool:
        """检查令牌是否有效"""
        pass
```

#### 2.2.2 服务发现模块 (Service Discovery Module)
```python
class PSMServiceDiscovery:
    """PSM 服务发现管理器"""

    def __init__(self, jwt_manager: JWTAuthManager):
        self.jwt_manager = jwt_manager
        self.regions = [
            "https://ms-neptune.byted.org",
            "https://ms-neptune.tiktok-us.org"
        ]

    async def search_service(self, keyword: str) -> Dict:
        """并发查询双区域服务"""
        # 实现并发查询逻辑
        pass
```

#### 2.2.3 MCP 工具模块 (MCP Tools Module)
```python
from mcp.server.fastmcp import FastMCP

class ByteDanceMCPServer:
    """字节跳动 MCP 服务器"""

    def __init__(self):
        self.mcp = FastMCP(
            name="byted-api",
            json_response=False,
            stateless_http=False
        )
        self.auth_manager = JWTAuthManager()
        self.service_discovery = PSMServiceDiscovery(self.auth_manager)

    def register_tools(self):
        """注册 MCP 工具"""
        pass
```

## 3. 接口设计

### 3.1 外部 API 接口

#### 3.1.1 JWT 认证接口
- **URL**: `https://cloud.bytedance.net/auth/api/v1/jwt`
- **方法**: GET
- **Headers**:
  ```
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
  Accept: application/json, text/plain, */*
  Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
  Cookie: CAS_SESSION={cookie_value}
  ```
- **响应**: JWT 令牌在响应头 `x-jwt-token` 中

#### 3.1.2 PSM 查询接口
- **URL**: `{region}/api/neptune/ms/service/search`
- **方法**: GET
- **Headers**:
  ```
  x-jwt-token: {jwt_token}
  ```
- **参数**:
  ```
  keyword: string  # 搜索关键词
  search_type: "all"  # 搜索类型
  ```

### 3.2 MCP 工具接口

#### 3.2.1 服务查询工具
```python
@mcp.tool()
async def search_psm_service(keyword: str) -> str:
    """搜索 PSM 服务信息

    Args:
        keyword: 服务关键词 (如: oec.affiliate.monitor)

    Returns:
        匹配的服务信息，包含 PSM、描述、负责人等
    """
```

#### 3.2.2 JWT 状态工具
```python
@mcp.tool()
async def check_jwt_status() -> str:
    """检查 JWT 令牌状态

    Returns:
        令牌有效性、过期时间等信息
    """
```

## 4. 数据模型

### 4.1 PSM 服务响应模型
```json
{
    "error_code": 0,
    "error_type": "",
    "error_message": "",
    "data": [
        {
            "psm": "oec.affiliate.monitor",
            "node_id": 9439321,
            "type": "thrift",
            "framework": "kitex",
            "service_chinese_name": "oec.affiliate.monitor",
            "description": "oec.affiliate.monitor",
            "owners": "wangzhonghua.97",
            "deployment_platform": "tce",
            "level": "P2",
            "platform_types": {
                "tce": "thrift"
            }
        }
    ]
}
```

### 4.2 错误响应模型
```json
{
    "error_code": 401,
    "error_type": "AUTH_ERROR",
    "error_message": "JWT token expired or invalid"
}
```

## 5. 并发处理策略

### 5.1 双区域并发查询
```python
async def concurrent_region_search(self, keyword: str) -> Dict:
    """并发查询双区域"""
    tasks = []

    for region in self.regions:
        url = f"{region}/api/neptune/ms/service/search"
        task = self._search_single_region(url, keyword)
        tasks.append(task)

    # 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 选择最佳结果
    return self._select_best_result(results)

def _select_best_result(self, results: List) -> Dict:
    """选择最佳查询结果"""
    for result in results:
        if isinstance(result, dict) and result.get("data"):
            return result
    return {"error": "No matching service found"}
```

### 5.2 超时与重试机制
- **单次请求超时**: 30 秒
- **总超时**: 60 秒
- **重试次数**: 2 次
- **退避策略**: 指数退避

## 6. 错误处理

### 6.1 错误分类
- **网络错误**: 连接超时、DNS 解析失败
- **认证错误**: JWT 令牌过期、无效令牌
- **服务错误**: 服务端 500 错误、维护中
- **业务错误**: 无匹配服务、参数错误

### 6.2 错误处理策略
```python
class MCPErrorHandler:
    """MCP 错误处理器"""

    async def handle_auth_error(self, error: Exception) -> str:
        """处理认证错误"""
        # 尝试重新获取 JWT 令牌
        pass

    async def handle_network_error(self, error: Exception) -> str:
        """处理网络错误"""
        # 实施重试机制
        pass

    def format_error_message(self, error: Exception) -> str:
        """格式化错误信息"""
        return f"Error: {str(error)}"
```

## 7. 性能优化

### 7.1 连接池管理
- 使用 `httpx.AsyncClient` 连接池
- 最大连接数: 100
- 连接保持时间: 30 秒
- 连接复用策略

### 7.2 缓存策略
- JWT 令牌缓存: 缓存至过期前 5 分钟
- 服务信息缓存: TTL 300 秒
- 缓存键设计: `psm:{keyword}:{region}`

### 7.3 异步处理
- 全程异步 IO 操作
- 避免阻塞调用
- 合理使用 `asyncio.gather()`

## 8. 安全设计

### 8.1 认证安全
- JWT 令牌加密存储
- Cookie 值环境变量注入
- 令牌过期自动刷新

### 8.2 网络安全
- HTTPS 强制使用
- 证书验证严格模式
- 请求头安全过滤

### 8.3 数据安全
- 敏感信息日志脱敏
- 错误信息不泄露内部细节
- 输入参数验证与清洗

## 9. 测试策略

### 9.1 单元测试
```python
class TestJWTAuthManager(unittest.TestCase):
    """JWT 认证管理器测试"""

    async def test_get_jwt_token_success(self):
        """测试 JWT 令牌获取成功"""
        pass

    async def test_get_jwt_token_failure(self):
        """测试 JWT 令牌获取失败"""
        pass

class TestPSMServiceDiscovery(unittest.TestCase):
    """PSM 服务发现测试"""

    async def test_concurrent_search_success(self):
        """测试并发查询成功"""
        pass

    async def test_concurrent_search_partial_failure(self):
        """测试并发查询部分失败"""
        pass
```

### 9.2 集成测试
- MCP 工具端到端测试
- 外部 API 集成测试
- 并发性能测试

### 9.3 性能测试
- 并发请求压力测试
- 内存使用监控
- 响应时间基准测试

## 10. 部署方案

### 10.1 环境配置
```bash
# 必需环境变量
export CAS_SESSION="your_cookie_value"

# 可选环境变量（有默认值）
export MCP_PORT=8123      # 默认: 8123
export LOG_LEVEL=INFO     # 默认: INFO
```

### 10.2 启动脚本
```bash
#!/bin/bash
# startup.sh - 后台启动 MCP 服务器

# 检查必需环境变量
if [ -z "$CAS_SESSION" ]; then
    echo "错误: CAS_SESSION 环境变量未设置"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动 MCP 服务器（后台模式）
nohup python main.py --port ${MCP_PORT:-8123} > mcp-server.log 2>&1 &

# 保存进程 ID
echo $! > mcp-server.pid
echo "MCP 服务器已启动，进程 ID: $!"
echo "日志文件: mcp-server.log"
```

### 10.3 停止脚本
```bash
#!/bin/bash
# stop.sh - 停止 MCP 服务器

if [ -f "mcp-server.pid" ]; then
    PID=$(cat mcp-server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        rm mcp-server.pid
        echo "MCP 服务器已停止"
    else
        echo "MCP 服务器未运行"
        rm -f mcp-server.pid
    fi
else
    echo "MCP 服务器未运行（找不到 pid 文件）"
fi
```

### 10.4 状态检查
```bash
#!/bin/bash
# status.sh - 检查 MCP 服务器状态

if [ -f "mcp-server.pid" ]; then
    PID=$(cat mcp-server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "MCP 服务器运行中，进程 ID: $PID"
        echo "端口: ${MCP_PORT:-8123}"
        echo "日志文件: mcp-server.log"
    else
        echo "MCP 服务器未运行（进程不存在）"
    fi
else
    echo "MCP 服务器未运行（找不到 pid 文件）"
fi
```

## 11. 迭代计划

### 11.1 第一阶段 (当前)
- [ ] JWT 认证模块
- [ ] 双区域并发查询
- [ ] 基础 MCP 工具
- [ ] 错误处理框架

### 11.2 第二阶段 (后续)
- [ ] 服务详情查询
- [ ] 批量服务查询
- [ ] 服务依赖分析
- [ ] 缓存优化

### 11.3 第三阶段 (扩展)
- [ ] 服务状态监控
- [ ] 历史数据查询
- [ ] 服务推荐算法
- [ ] 多语言支持

## 12. 风险评估

### 12.1 技术风险
- **API 变更风险**: 外部 API 接口可能变更
- **性能风险**: 并发查询可能导致性能问题
- **依赖风险**: 第三方库安全漏洞

### 12.2 缓解措施
- API 版本控制与适配层
- 性能监控与自动降级
- 定期依赖更新与安全扫描