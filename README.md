# MCP Services

MCP (Model Context Protocol) 服务集合，为 AI 应用提供标准化数据接口。

## 服务列表

| 服务 | 状态 | 端口 | 描述 |
|------|------|------|------|
| [stock](stock) | ✅ | 8124 | 中国股市数据查询 |
| [image2text](image2text) | ✅ | - | 图像转文本处理 |
| [byted-api](byted-api) | ✅ | - | 字节跳动 API 集成 |

## 快速开始

```bash
# 启动股票服务
cd stock && ./start.sh -d

# 查看服务状态
./stop.sh -s
```

## 集成配置

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "stock-data": {
      "command": "python",
      "args": ["/path/to/mcp/stock/stock_mcp_server.py", "--port", "8124"]
    }
  }
}
```

## 许可证

MIT License
zzz
