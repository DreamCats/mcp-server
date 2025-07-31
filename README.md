# MCP Services Hub

一个集中管理多种 MCP (Model Context Protocol) 服务的项目，为 AI 大模型提供各类专业领域的数据查询和工具调用能力。

## 项目概述

本项目是一个 MCP 服务集合，旨在为 AI 应用提供标准化、模块化的专业服务接口。每个服务都遵循 MCP 协议标准，可以独立部署和使用，也可以组合使用以构建更强大的 AI 工作流。

## 设计理念

### 🎯 模块化架构
- 每个服务独立开发和部署
- 统一的 MCP 协议标准
- 可组合的服务生态
- 便于扩展和维护

### 🚀 MCP 协议支持
- 完全兼容 MCP (Model Context Protocol) 标准
- 支持 HTTP/SSE 传输方式
- 可与 Claude Desktop、自定义 MCP 客户端无缝集成
- 提供标准化的工具调用接口

### 🛠 开发友好
- 基于 FastMCP 框架，开发简单高效
- 统一的项目结构和开发规范
- 完整的启动/停止脚本，支持后台运行
- 详细的日志记录和错误处理

## 项目结构

```
mcp/
├── README.md                    # 项目总体说明文档
├── .gitignore                   # Git 忽略文件配置
├── stock/                       # 📈 股票金融数据 MCP 服务
│   ├── README.md                # 详细功能说明
│   ├── USAGE.md                 # 使用指南
│   ├── stock_mcp_server.py      # 主服务文件
│   ├── requirements.txt         # Python 依赖
│   ├── start.sh                 # 启动脚本
│   ├── stop.sh                  # 停止脚本
│   ├── test.py                  # 基础功能测试
│   ├── test_mcp_client.py       # MCP 客户端测试
│   ├── claude_desktop_config.json # Claude Desktop 配置示例
│   └── demo.sh                  # 演示脚本
├── [future-service]/            # 🔮 未来的其他 MCP 服务
│   ├── README.md                # 服务说明文档
│   ├── requirements.txt         # 服务依赖
│   ├── server.py                # 服务主文件
│   └── ...                      # 其他服务文件
└── docs/                        # 📚 项目文档
    ├── mcp-protocol.md          # MCP 协议说明
    ├── development-guide.md     # 开发指南
    └── deployment.md            # 部署指南
```

## 可用服务

### 📈 Stock MCP Service (股票金融数据服务)

**状态**: ✅ 已完成
**端口**: 8124
**功能**: 提供中国股市数据查询能力

#### 主要功能
- 历史行情查询（日/周/月频率）
- 分时数据获取（1/5/15/30/60分钟）
- 股票基本信息查询
- 筹码分布分析
- 资金流向分析（个股/概念/行业）
- 市场热点和龙虎榜数据

#### 快速启动
```bash
cd stock
./start.sh -d  # 后台运行
```

详细信息请参考: [`stock/README.md`](stock/README.md)

### 🔮 未来规划的服务

以下是计划开发的其他 MCP 服务：

#### 📰 News MCP Service (新闻资讯服务)
- **状态**: 🚧 规划中
- **功能**: 提供实时新闻、财经资讯查询
- **数据源**: 新闻API、RSS源

#### 🌤️ Weather MCP Service (天气数据服务)
- **状态**: 🚧 规划中
- **功能**: 天气查询、气象预报
- **数据源**: 天气API

#### 🔍 Search MCP Service (搜索服务)
- **状态**: 🚧 规划中
- **功能**: 网络搜索、知识库查询
- **数据源**: 搜索引擎API

#### 📊 Analytics MCP Service (数据分析服务)
- **状态**: 🚧 规划中
- **功能**: 数据处理、统计分析、可视化
- **工具**: pandas、matplotlib、plotly

## 快速开始

### 1. 环境要求

- Python 3.8+
- 网络连接
- Git（用于克隆项目）

### 2. 克隆项目

```bash
git clone <repository-url>
cd mcp
```

### 3. 选择并启动服务

```bash
# 启动股票服务
cd stock
./start.sh -d

# 查看服务状态
./stop.sh -s
```

## MCP 客户端集成

### Claude Desktop 集成

在 Claude Desktop 配置文件中添加多个服务：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stock-data": {
      "command": "python",
      "args": ["/path/to/mcp/stock/stock_mcp_server.py", "--port", "8124"],
      "env": {}
    },
    "news-service": {
      "command": "python",
      "args": ["/path/to/mcp/news/news_mcp_server.py", "--port", "8125"],
      "env": {}
    }
  }
}
```

### HTTP 客户端集成

```json
{
  "mcpServers": {
    "stock-data": {
      "transport": "http",
      "url": "http://localhost:8124/mcp"
    },
    "news-service": {
      "transport": "http",
      "url": "http://localhost:8125/mcp"
    }
  }
}
```

## 服务管理

### 批量启动服务

```bash
# 创建启动所有服务的脚本
#!/bin/bash
echo "启动 MCP 服务..."

# 启动股票服务
cd stock && ./start.sh -d && cd ..
echo "✅ 股票服务已启动 (端口: 8124)"

# 启动其他服务（未来）
# cd news && ./start.sh -d && cd ..
# echo "✅ 新闻服务已启动 (端口: 8125)"

echo "🚀 所有服务启动完成"
```

### 服务状态检查

```bash
# 检查所有服务状态
./scripts/check_services.sh

# 或单独检查
cd stock && ./stop.sh -s
```

## 开发新的 MCP 服务

### 服务开发规范

每个 MCP 服务应遵循以下结构：

```
service-name/
├── README.md                    # 服务说明文档
├── USAGE.md                     # 使用指南
├── server.py                    # 主服务文件
├── requirements.txt             # Python 依赖
├── start.sh                     # 启动脚本
├── stop.sh                      # 停止脚本
├── test.py                      # 基础功能测试
├── test_mcp_client.py           # MCP 客户端测试
└── config/                      # 配置文件目录
    └── config.json              # 服务配置
```

### 开发步骤

1. **创建服务目录**
   ```bash
   mkdir new-service
   cd new-service
   ```

2. **实现 MCP 服务器**
   ```python
   from mcp.server.fastmcp import FastMCP

   mcp = FastMCP(name="new-service")

   @mcp.tool()
   def your_tool_function(param: str) -> str:
       """工具函数描述"""
       return "result"
   ```

3. **添加启动脚本**
   ```bash
   cp ../stock/start.sh ./
   cp ../stock/stop.sh ./
   # 修改端口和服务名称
   ```

4. **编写文档和测试**

### 技术栈

- **MCP 框架**: [FastMCP](https://github.com/pydantic/fastmcp)
- **Web 框架**: FastAPI + Uvicorn
- **数据处理**: pandas, numpy
- **HTTP 客户端**: httpx
- **配置管理**: pydantic-settings

## 部署选项

### 单服务部署

```bash
# 部署特定服务
cd stock
./start.sh -d
```

### 多服务部署

```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 或使用脚本批量启动
./scripts/start_all_services.sh
```

### 生产环境

建议配置：
- 反向代理（Nginx）
- HTTPS 证书
- 服务监控
- 日志聚合

详细配置请参考各服务的 README.md。

## 贡献指南

### 添加新服务

1. Fork 本项目
2. 创建新的服务目录
3. 按照开发规范实现服务
4. 添加完整的文档和测试
5. 提交 Pull Request

### 改进现有服务

1. 在对应服务目录下进行修改
2. 确保测试通过
3. 更新相关文档
4. 提交 Pull Request

## 许可证

MIT License

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 讨论交流: [GitHub Discussions]

---

### 服务详细文档

- 📈 **股票服务**: [`stock/README.md`](stock/README.md) | [`stock/USAGE.md`](stock/USAGE.md)
- 📰 **新闻服务**: `news/README.md` (规划中)
- 🌤️ **天气服务**: `weather/README.md` (规划中)

### 开发文档

- 🔧 **开发指南**: `docs/development-guide.md` (待创建)
- 📋 **MCP 协议**: `docs/mcp-protocol.md` (待创建)
- 🚀 **部署指南**: `docs/deployment.md` (待创建)
