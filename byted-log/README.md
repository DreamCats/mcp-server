# 字节跳动日志查询 MCP 服务器

一个专门的模型上下文协议（MCP）服务器，为字节跳动内部日志系统提供跨区域的认证日志查询能力（支持美国和新加坡区域）。

## 🌟 项目概述

该 MCP 服务器作为 MCP 客户端与字节跳动日志服务之间的桥梁，通过基于 JWT 的认证实现按日志 ID 的安全查询。支持在不同区域部署中进行并发查询，并提供用户友好的格式化响应。

## 🏗️ 架构设计

### 核心组件

- **FastMCP 框架**: 现代化的 MCP 服务器实现，支持异步操作
- **动态认证**: 基于 CAS_SESSION Cookie 的每请求 JWT 令牌管理
- **多区域支持**: 美国 TTP 和国际（新加坡）区域日志服务
- **会话隔离**: 每个客户端的认证上下文和适当的资源清理

### 关键文件

```
src/
├── mcp_server.py           # 主 MCP 服务器和工具注册
├── auth.py                # JWT 认证管理器
├── log_query_by_id.py     # 基于日志ID的查询功能 (v1/trace API)
├── log_query_by_keyword.py  # 基于关键词的查询功能 (v2/log API)
└── __init__.py            # 包初始化

main.py                    # 服务器入口点和 HTTP 设置
tests/                     # 使用真实数据的综合测试套件
scripts/                   # 部署管理脚本
restart.sh                 # 服务重启脚本
```

## 🚀 功能特性

### 核心功能
- ✅ **日志 ID 查询**: 跨区域按唯一 logid 查询日志 (v1/trace API)
- ✅ **关键词查询**: 基于关键词和时间范围的日志过滤查询 (v2/log API)
- ✅ **多区域支持**: 美国和国际（新加坡）区域
- ✅ **PSM 服务过滤**: 按产品服务模块（PSM）服务过滤
- ✅ **基于时间的查询**: 可配置的扫描时间范围（默认：10 分钟）
- ✅ **关键词过滤**: 支持包含和排除关键词，区分大小写
- ✅ **并发处理**: 跨多个区域的并行查询

### 认证与安全
- ✅ **JWT 令牌管理**: 自动令牌获取和刷新
- ✅ **基于 Cookie 的认证**: 支持区域特定变体的 CAS_SESSION Cookie
- ✅ **会话隔离**: 每个客户端的认证上下文
- ✅ **安全头部处理**: 动态每请求头部提取

### 响应与格式化
- ✅ **消息提取**: 从日志中智能提取 _msg 字段
- ✅ **元数据处理**: 时间戳、服务信息和日志级别
- ✅ **用户友好的输出**: 中文 Markdown 格式化响应
- ✅ **错误处理**: 带有故障排除指导的详细错误消息

## 🔧 安装配置

### 前提条件
- Python 3.8+
- pip 包管理器

### 设置步骤
```bash
# 克隆仓库
git clone <repository-url>
cd bytedance-log-mcp

# 安装依赖
pip install -r requirements.txt

# 设置环境变量（可选）
export CAS_SESSION_US="your-us-session-cookie"
export CAS_SESSION_I18N="your-international-session-cookie"
```

## 🎯 使用方法

### 启动服务器

#### 开发模式
```bash
python main.py --host 0.0.0.0 --port 8080 --log-level INFO
```

#### 生产模式（后台服务）
```bash
# 启动服务
./scripts/startup.sh

# 检查状态
./scripts/status.sh

# 停止服务
./scripts/stop.sh

# 重启服务
./restart.sh
```

### MCP 工具使用

服务器公开两个主要工具：

#### 1. `query_logs_by_logid` - 基于日志ID查询 (v1/trace API)
**参数说明：**
- `logid`（必需）：唯一日志标识符
- `region`（必需）：目标区域（`us` 或 `i18n`）
- `psm_list`（可选）：要过滤的 PSM 服务列表，逗号分隔
- `scan_time_min`（可选）：扫描时间范围（分钟，默认：10）

**使用示例：**
```python
# 使用 MCP 客户端
result = await mcp_client.call_tool(
    "query_logs_by_logid",
    {
        "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
        "region": "us",
        "psm_list": "ttec.script.live_promotion_change",
        "scan_time_min": 10
    }
)
```

#### 2. `query_logs_by_keyword` - 基于关键词查询 (v2/log API)
**参数说明：**
- `region`（必需）：目标区域（`us` 或 `i18n`）
- `psm_list`（必需）：要过滤的 PSM 服务列表，逗号分隔（必填）
- `start_time`（可选）：开始时间戳（秒级，默认：1小时前）
- `end_time`（可选）：结束时间戳（秒级，默认：当前时间）
- `keyword_filter_include`（可选）：包含关键词列表，逗号分隔
- `keyword_filter_exclude`（可选）：排除关键词列表，逗号分隔
- `limit`（可选）：返回结果数量限制（默认：100，最大：1000）

**使用示例：**
```python
# 查询包含错误关键词的日志
result = await mcp_client.call_tool(
    "query_logs_by_keyword",
    {
        "region": "us",
        "psm_list": "ttec.script.live_promotion_change",
        "start_time": 1704067200,  # 2024-01-01 00:00:00
        "end_time": 1704153600,    # 2024-01-02 00:00:00
        "keyword_filter_include": "error,exception,failed",
        "keyword_filter_exclude": "debug,info",
        "limit": 50
    }
)
```

### 认证方式

服务器支持多种认证方法：

1. **区域特定 Cookie**：`COOKIE_US`、`COOKIE_I18N` 头部
2. **默认 Cookie**：`cookie` 或 `Cookie` 头部
3. **环境变量**：`CAS_SESSION_US`、`CAS_SESSION_I18N`

优先级：区域特定 > 默认 Cookie > 环境变量

## 🧪 测试

### 运行所有测试
```bash
python -m pytest tests/ -v
```

### 运行特定测试
```bash
python -m pytest tests/test_real_data_workflow.py::TestRealDataWorkflow::test_real_data_success_workflow -v
```

### 生成测试报告
```bash
python tests/run_tests.py
```

### 测试覆盖范围
- ✅ 使用真实数据的成功工作流
- ✅ 认证错误处理
- ✅ Cookie 缺失场景
- ✅ 区域特定 Cookie 优先级
- ✅ 多 PSM 服务支持
- ✅ 异常处理和错误响应
- ✅ 关键词查询功能测试
- ✅ 时间范围查询测试

## 📋 配置说明

### 环境变量

| 变量名 | 描述 | 必需 | 默认值 |
|----------|-------------|----------|---------|
| `MCP_HOST` | 服务器主机地址 | 否 | `0.0.0.0` |
| `MCP_PORT` | 服务器端口 | 否 | `8080` |
| `MCP_LOG_LEVEL` | 日志级别（DEBUG/INFO/WARNING/ERROR） | 否 | `INFO` |
| `LOG_FORMAT` | 日志格式（json/console） | 否 | `json` |
| `CAS_SESSION_US` | 美国区域 CAS 会话 Cookie | 否 | - |
| `CAS_SESSION_I18N` | 国际区域 CAS 会话 Cookie | 否 | - |

### 区域端点

| 区域 | 端点地址 | 虚拟区域 |
|--------|----------|-----------------|
| `us` | `https://logservice-tx.tiktok-us.org` | US-TTP, US-TTP2, US-East |
| `i18n` | `https://logservice-sg.tiktok-row.org` | Singapore-Common, Singapore-Central |

## 🔍 API 参考

### 日志查询响应格式

```json
{
  "status": "success",
  "region": "us",
  "total": 3,
  "logs": [
    {
      "logid": "02176355661407900000000000000000000ffff0a71b1e8a4db84",
      "message": "Live promotion change event processed successfully",
      "psm": "ttec.script.live_promotion_change",
      "timestamp": "2024-01-15T10:30:45Z",
      "level": "INFO",
      "details": {
        "promotion_id": "promo_12345",
        "status": "active"
      }
    }
  ]
}
```

### 错误响应格式

```
❌ 查询 logid [logid] 失败
错误详情: [具体错误信息]
建议: [解决建议]
```

## 🛠️ 开发指南

### 项目结构
```
bytedance-log-mcp/
├── src/
│   ├── mcp_server.py           # MCP 服务器实现
│   ├── auth.py                # JWT 认证
│   ├── log_query_by_id.py     # 基于日志ID的查询逻辑 (v1/trace API)
│   ├── log_query_by_keyword.py  # 基于关键词的查询逻辑 (v2/log API)
│   └── __init__.py
├── tests/
│   ├── test_real_data_workflow.py  # 主测试套件
│   ├── conftest.py           # 测试配置
│   └── run_tests.py          # 测试运行器
├── scripts/
│   ├── startup.sh            # 服务启动
│   ├── stop.sh              # 服务停止
│   └── status.sh            # 状态检查
├── main.py                   # 服务器入口
├── restart.sh                # 服务重启脚本
├── requirements.txt          # 依赖包
└── README.md                # 本文档
```

### 开发设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行代码格式化
black src/ tests/
isort src/ tests/

# 运行代码检查
flake8 src/ tests/
```

## 🔒 安全注意事项

- **Cookie 安全**: 切勿将会话 Cookie 提交到版本控制
- **JWT 令牌管理**: 令牌在过期前自动刷新
- **会话隔离**: 每个客户端获得独立的认证上下文
- **资源清理**: 认证资源的正确清理

## 🐛 故障排除

### 常见问题

1. **认证失败**
   - 验证 CAS_SESSION Cookie 是否有效且未过期
   - 检查区域特定 Cookie 优先级设置
   - 确保请求中的头部格式正确

2. **不支持的区域**
   - 有效区域：`us`、`i18n`
   - 检查区域参数拼写和大小写

3. **未找到日志（基于ID查询）**
   - 验证 logid 格式和存在性
   - 检查 scan_time_min 参数（如有需要可增加）
   - 验证 PSM 服务名称

4. **未找到日志（基于关键词查询）**
   - 检查关键词拼写是否正确
   - 扩大时间范围（start_time, end_time）
   - 验证 PSM 服务名称是否正确
   - 尝试不同的虚拟区域（vregion）
   - 调整关键词过滤条件

5. **服务启动问题**
   - 检查端口可用性：`lsof -i :8080`
   - 验证 Python 依赖：`pip check`
   - 查看 `/tmp/mcp_server.log` 中的日志

### 调试模式
```bash
# 启用调试日志
export MCP_LOG_LEVEL=DEBUG
python main.py --log-level DEBUG

# 使用控制台彩色格式（适合开发环境）
python main.py --log-format console

# 使用JSON格式（适合生产环境）
python main.py --log-format json
```

## 🤝 贡献指南

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature-name`
3. 进行修改并添加测试
4. 运行测试套件：`python -m pytest tests/`
5. 提交 Pull Request

## 📄 许可证

本项目属于字节跳动专有，仅供内部使用。

## 📞 支持

如有问题和疑问：
- 查看故障排除部分
- 查看测试用例获取使用示例
- 在调试模式下检查日志
- 联系开发团队

---

**注意**: 此 MCP 服务器专为字节跳动内部日志基础设施设计，需要有效的认证凭据才能正常运行。