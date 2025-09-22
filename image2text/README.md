# image2text MCP Server

一个基于MCP (Model Context Protocol) 的图片转文本服务器，为Claude Code提供图片理解能力。

## 功能特性

- 🖼️ **图片文本提取**: 从图片中提取文字内容
- 🔍 **图片内容分析**: 支持多种分析类型（通用、文本、物体、场景）
- 🌐 **OpenAI兼容API**: 支持任何OpenAI兼容的视觉模型API
- ⚙️ **灵活配置**: 支持通过HTTP headers动态配置API参数
- 🧪 **完整测试**: 包含全面的单元测试
- 📊 **监控日志**: 详细的日志记录和错误处理

## 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

```bash
# 设置默认API配置
export IMAGE2TEXT_DEFAULT_API_KEY="your_api_key"
export IMAGE2TEXT_DEFAULT_API_BASE="https://your.api.endpoint"
export IMAGE2TEXT_DEFAULT_MODEL_ID="your_model_id"
```

### 3. 启动服务器

```bash
# 启动MCP服务器（默认端口8201）
python src/main.py

# 自定义端口和主机
python src/main.py --port 8080 --host 127.0.0.1

# 调试模式
python src/main.py --log-level DEBUG
```

## 使用方法

### MCP工具调用

服务器提供以下MCP工具：

#### 1. extract_text_from_image - 提取图片文本

```json
{
  "tool": "extract_text_from_image",
  "arguments": {
    "image_data": "base64_encoded_image_data",
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "your_api_key",
    "model_id": "gpt-4-vision-preview",
    "prompt": "请描述这张图片"
  }
}
```

#### 2. analyze_image_content - 分析图片内容

```json
{
  "tool": "analyze_image_content",
  "arguments": {
    "image_data": "base64_encoded_image_data",
    "analysis_type": "general",
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "your_api_key",
    "model_id": "gpt-4-vision-preview"
  }
}
```

分析类型：
- `general`: 通用描述（默认）
- `text`: 文本提取
- `objects`: 物体识别
- `scene`: 场景分析

#### 3. get_supported_formats - 获取支持的格式

```json
{
  "tool": "get_supported_formats",
  "arguments": {}
}
```

### 使用curl测试

```bash
# 测试图片文本提取
curl -X POST http://localhost:8201/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "extract_text_from_image",
    "arguments": {
      "image_data": "your_base64_image_data",
      "prompt": "请描述这张图片的内容"
    }
  }'

# 测试图片内容分析
curl -X POST http://localhost:8201/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "analyze_image_content",
    "arguments": {
      "image_data": "your_base64_image_data",
      "analysis_type": "text"
    }
  }'
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|---------|
| IMAGE2TEXT_DEFAULT_API_BASE | 默认API基础地址 | https://api.openai.com/v1 |
| IMAGE2TEXT_DEFAULT_API_KEY | 默认API密钥 | None |
| IMAGE2TEXT_DEFAULT_MODEL_ID | 默认模型ID | gpt-4-vision-preview |
| IMAGE2TEXT_SERVER_PORT | 服务器端口 | 8201 |
| IMAGE2TEXT_SERVER_HOST | 服务器主机地址 | 0.0.0.0 |
| IMAGE2TEXT_MAX_IMAGE_SIZE | 最大图片大小（字节） | 10485760 (10MB) |

### 支持的图片格式

- JPEG (image/jpeg)
- PNG (image/png)
- WebP (image/webp)

### API参数传递

支持通过HTTP headers动态传递API参数：

- `X-API-Base`: API基础地址
- `X-API-Key`: API密钥
- `X-Model-ID`: 模型ID

## 开发指南

### 项目结构

```
image2text_mcp/
├── src/
│   ├── __init__.py
│   ├── main.py              # MCP服务器主入口
│   ├── config.py            # 配置管理
│   ├── image_processor.py   # 图片处理核心逻辑
│   ├── api_client.py        # API客户端封装
│   └── utils.py             # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_main.py         # 主模块测试
│   ├── test_config.py       # 配置模块测试
│   ├── test_api_client.py   # API客户端测试
│   └── test_image_processor.py # 图片处理器测试
├── requirements.txt         # 项目依赖
├── pyproject.toml          # 项目配置
└── README.md              # 项目文档
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_image_processor.py

# 运行测试并显示详细信息
pytest -v tests/

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

### 代码规范

- 所有公共方法必须有中文注释
- 使用类型提示（Type Hints）
- 遵循PEP 8代码风格
- 包含完整的错误处理
- 编写单元测试

## 错误处理

### 常见错误码

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| 400 | 图片格式不支持 | 检查图片格式 |
| 413 | 图片大小超限 | 压缩或缩小图片 |
| 401 | API密钥无效 | 检查API密钥配置 |
| 429 | API频率限制 | 稍后重试 |
| 500 | 服务器内部错误 | 查看日志信息 |

### 错误信息格式

```json
{
  "error": "错误类型: 详细错误信息",
  "suggestion": "建议的解决方案"
}
```

## 性能优化

### 缓存策略
- 相同图片的重复请求会进行缓存
- 缓存TTL为1小时
- 支持LRU缓存淘汰

### 并发处理
- 使用asyncio处理并发请求
- 支持连接池复用
- 实现请求重试机制

### 监控指标
- API调用次数和响应时间
- 错误率和成功率
- 图片处理吞吐量

## 安全考虑

- API密钥通过环境变量或headers传递，不硬编码
- 图片大小限制防止DoS攻击
- 输入验证和清理
- 详细的访问日志

## 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- 🚀 支持基本的图片文本提取
- 🔧 支持多种分析类型
- 📊 完整的错误处理和日志
- 🧪 全面的单元测试覆盖

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如有问题或建议，请提交 Issue 或联系维护者。

---

**注意**: 使用此工具需要有效的视觉模型API密钥。请确保遵守相关API服务条款和使用限制。