# ByteDance Live Promotion MCP 服务器

集成字节跳动内部服务发现系统的 Model Context Protocol (MCP) 服务器，提供基于 JWT 的身份验证和 PSM（产品、子系统、模块）服务查找功能。

## 功能特性

- **JWT 身份验证**: 与字节跳动认证服务的安全身份验证
- **PSM 服务发现**: 并发搜索多个区域的服务
- **MCP 工具**: 四个主要工具用于服务发现和身份验证管理
- **流式 HTTP 传输**: 基于 FastMCP 的现代异步架构

## Quick Start

### Prerequisites

- Python 3.8+
- ByteDance internal network access
- Valid `CAS_SESSION` cookie

### Installation

```bash
# Clone and setup
git clone <repository>
cd byted-live-promotion

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install mcp fastapi uvicorn httpx structlog
```

### Configuration

Set your ByteDance authentication cookie:

```bash
export CAS_SESSION="your_cookie_value_here"
```

### 启动方式

#### 方法1: 使用启动脚本 (推荐)

```bash
# 赋予执行权限
chmod +x startup.sh

# 启动 MCP 服务器（后台模式）
./startup.sh

# 查看运行状态
tail -f mcp-server.log

# 停止服务器
kill $(cat mcp-server.pid)
```

#### 方法2: 直接运行

```bash
python main.py --port 8123
```

#### 启动脚本功能

`startup.sh` 提供了完整的后台启动功能：

- ✅ **环境检查**: 验证 `CAS_SESSION` 和虚拟环境
- ✅ **进程管理**: 防止重复启动，保存进程ID
- ✅ **日志管理**: 输出重定向到 `mcp-server.log`
- ✅ **状态检测**: 启动后自动检查服务状态
- ✅ **端口配置**: 支持 `MCP_PORT` 环境变量自定义端口

**使用示例：**
```bash
# 自定义端口启动
export MCP_PORT=8080
./startup.sh

# 查看日志
tail -f mcp-server.log

# 停止服务
kill $(cat mcp-server.pid)
rm -f mcp-server.pid
```

## 可用工具

### 1. `search_psm_service`
使用并发区域查询搜索 PSM 服务信息。

**使用方法：**
```
search_psm_service("oec.affiliate.monitor")
```

**返回：** 服务详情，包括 PSM、描述、所有者、框架和部署平台。

### 2. `check_jwt_status`
检查 JWT 令牌状态和有效性。

**使用方法：**
```
check_jwt_status()
```

**返回：** 令牌有效性、过期时间和自动刷新状态。

### 3. `list_available_regions`
列出服务发现的可用区域。

**使用方法：**
```
list_available_regions()
```

**返回：** 配置的区域和查询模式信息。

### 4. `search_multiple_services`
并发搜索多个 PSM 服务。

**使用方法：**
```
search_multiple_services("oec.affiliate.monitor, oec.affiliate.api")
```

**返回：** 所有服务的结果和关键信息。

## 架构说明

### 核心组件

- **JWT 身份验证层**: 从字节跳动认证服务获取令牌
- **PSM 服务发现**: 跨区域搜索 Neptune 服务注册表
- **MCP 服务器框架**: 基于 FastMCP 的流式 HTTP 传输

### 服务发现流程

1. **并发查询**: 同时搜索两个区域：
   - `https://ms-neptune.byted.org/api/neptune/ms/service/search`
   - `https://ms-neptune.tiktok-us.org/api/neptune/ms/service/search`

2. **结果选择**: 返回具有匹配 PSM 的端点结果

3. **错误处理**: 全面的错误处理和用户友好的消息提示

## 开发指南

### 项目结构

```
byted-live-promotion/
├── main.py                 # 入口文件
├── src/
│   ├── mcp_server.py      # MCP 服务器实现
│   ├── auth.py            # JWT 身份验证
│   └── service_discovery.py # PSM 服务发现
├── test.py                # 身份验证测试脚本
├── startup.sh             # 启动脚本
└── README.md
```

### 身份验证测试

```bash
python test.py
```

### 命令行选项

```bash
python main.py --help

选项:
  --port PORT          监听端口 (默认: 8123)
  --host HOST          绑定主机 (默认: localhost)
  --log-level LEVEL    日志级别: DEBUG, INFO, WARNING, ERROR (默认: INFO)
```

## 安全说明

- JWT 令牌从环境特定的 cookie 值获取
- 服务发现需要有效的 JWT 身份验证
- 所有 API 调用都包含适当的错误处理和超时
- 不记录或暴露凭据

## 错误处理

服务器为常见问题提供详细的错误消息：

- **JWT 无效**: 检查 `CAS_SESSION` 环境变量
- **服务未找到**: 验证 PSM 名称拼写
- **网络问题**: 检查字节跳动内部网络连接
- **身份验证失败**: 确保有效的会话 cookie

## 依赖要求

- `mcp>=1.0.0`
- `fastapi>=0.104.0`
- `uvicorn>=0.24.0`
- `httpx>=0.25.0`
- `structlog>=23.0.0`

## MCP 客户端连接配置

本服务器使用 HTTP 协议暴露 MCP 接口，支持多种客户端连接方式。

### HTTP 协议端点

服务器启动后提供以下 HTTP 端点：

- **MCP 工具接口**: `http://localhost:8123/mcp`
- **SSE 流式接口**: `http://localhost:8123/sse`
- **健康检查**: `http://localhost:8123/health` (如果实现)

### Claude Desktop 配置 (HTTP 模式)

在 Claude Desktop 中添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "byted-live-promotion": {
      "command": "python",
      "args": ["/path/to/byted-live-promotion/main.py", "--port", "8123"],
      "env": {
        "CAS_SESSION": "your_cookie_value_here"
      }
    }
  }
}
```

### 配置文件位置

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 直接使用 HTTP 客户端

可以使用任何 HTTP 客户端直接调用 MCP 接口：

```bash
# 调用 search_psm_service 工具
curl -X POST http://localhost:8123/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_psm_service",
    "arguments": {
      "keyword": "oec.affiliate.monitor"
    }
  }'

# 检查 JWT 状态
curl -X POST http://localhost:8123/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "check_jwt_status",
    "arguments": {}
  }'
```

### Python HTTP 客户端示例

```python
import requests
import json

# MCP 服务器地址
MCP_SERVER_URL = "http://localhost:8123/mcp"

def call_mcp_tool(tool_name, arguments):
    """调用 MCP 工具"""
    payload = {
        "tool": tool_name,
        "arguments": arguments
    }

    response = requests.post(MCP_SERVER_URL, json=payload)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 搜索服务
    result = call_mcp_tool("search_psm_service", {"keyword": "oec.affiliate.monitor"})
    print("搜索结果:", result)

    # 检查 JWT 状态
    jwt_status = call_mcp_tool("check_jwt_status", {})
    print("JWT 状态:", jwt_status)
```

### JavaScript/Node.js HTTP 客户端示例

```javascript
const axios = require('axios');

const MCP_SERVER_URL = 'http://localhost:8123/mcp';

async function callMcpTool(toolName, arguments) {
    try {
        const response = await axios.post(MCP_SERVER_URL, {
            tool: toolName,
            arguments: arguments
        });
        return response.data;
    } catch (error) {
        console.error('MCP 调用失败:', error.message);
        throw error;
    }
}

// 使用示例
async function main() {
    // 搜索服务
    const result = await callMcpTool('search_psm_service', {
        keyword: 'oec.affiliate.monitor'
    });
    console.log('搜索结果:', result);

    // 检查 JWT 状态
    const jwtStatus = await callMcpTool('check_jwt_status', {});
    console.log('JWT 状态:', jwtStatus);
}

main().catch(console.error);
```

### 环境变量配置

确保在运行环境中设置必要的环境变量：

```bash
# 必需
export CAS_SESSION="your_cookie_value"

# 可选
export MCP_PORT="8123"          # 自定义端口
export LOG_LEVEL="INFO"         # 日志级别
```

### 连接测试

**测试 HTTP 连接：**

```bash
# 测试服务器是否运行
curl -I http://localhost:8123/health

# 测试工具调用
curl -X POST http://localhost:8123/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_available_regions", "arguments": {}}'
```

**Claude Desktop 中测试：**

1. 重启 Claude Desktop
2. 查看工具列表中是否出现 `search_psm_service` 等工具
3. 使用 `check_jwt_status` 工具测试连接状态

### 故障排除

**连接失败时检查：**

1. ✅ 验证 `CAS_SESSION` 环境变量已设置
2. ✅ 确认 MCP 服务器正在运行 (`ps aux | grep main.py`)
3. ✅ 检查端口是否被占用 (`netstat -an | grep 8123`)
4. ✅ 查看日志文件 `mcp-server.log` 中的错误信息
5. ✅ 测试 HTTP 端点是否可访问：`curl -I http://localhost:8123/mcp`

**常见错误：**

- `Connection refused`: 检查服务器是否启动，端口是否正确
- `ModuleNotFoundError`: 确保虚拟环境已激活
- `Invalid JWT`: 更新 `CAS_SESSION` 环境变量
- `HTTP 404`: 检查端点 URL 是否正确
- `HTTP 500`: 查看服务器日志了解详细错误信息

## 许可证

仅限字节跳动内部使用。