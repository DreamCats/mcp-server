# 使用说明

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务器
```bash
# 启动服务器
./start.sh

# 查看实时日志
tail -f logs/server.log
```

### 3. 停止服务器
```bash
./stop.sh
```

### 4. 运行测试
```bash
# 运行所有测试
PYTHONPATH=src python -m pytest tests/ -v

# 运行特定测试
PYTHONPATH=src python -m pytest tests/test_main.py -v
```

### 5. 使用示例
```bash
# 运行示例客户端
python example_usage.py
```

## 配置说明

### 环境变量
服务器支持以下环境变量（前缀为 `IMAGE2TEXT_`）：

- `IMAGE2TEXT_DEFAULT_API_BASE`: API基础地址（默认：https://api.openai.com/v1）
- `IMAGE2TEXT_DEFAULT_API_KEY`: API密钥
- `IMAGE2TEXT_DEFAULT_MODEL_ID`: 模型ID（默认：gpt-4-vision-preview）
- `IMAGE2TEXT_SERVER_PORT`: 服务器端口（默认：8201）
- `IMAGE2TEXT_SERVER_HOST`: 服务器主机（默认：0.0.0.0）
- `IMAGE2TEXT_MAX_IMAGE_SIZE`: 最大图片大小，单位字节（默认：10MB）

### 创建环境配置文件
```bash
# 创建 .env 文件
cat > .env << EOF
IMAGE2TEXT_DEFAULT_API_KEY=your-api-key-here
IMAGE2TEXT_DEFAULT_API_BASE=https://api.openai.com/v1
IMAGE2TEXT_DEFAULT_MODEL_ID=gpt-4-vision-preview
EOF
```

## API 使用

### 基本图片文本提取
```python
import requests

response = requests.post("http://localhost:8201/mcp", json={
    "tool": "extract_text_from_image",
    "arguments": {
        "image_data": "base64_encoded_image_data",
        "prompt": "请描述这张图片的内容"
    }
})
```

### 使用自定义API参数
```python
response = requests.post("http://localhost:8201/mcp", json={
    "tool": "extract_text_from_image",
    "arguments": {
        "image_data": "base64_encoded_image_data",
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "your-api-key",
        "model_id": "gpt-4-vision-preview",
        "prompt": "请详细描述这张图片的内容"
    }
})
```

### 图片内容分析
```python
response = requests.post("http://localhost:8201/mcp", json={
    "tool": "analyze_image_content",
    "arguments": {
        "image_data": "base64_encoded_image_data",
        "analysis_type": "general"  # general, text, objects, scene
    }
})
```

## 故障排除

### 端口被占用
```bash
# 查看占用端口的进程
lsof -i :8201

# 强制停止
./stop.sh
```

### 查看日志
```bash
# 实时查看日志
tail -f logs/server.log

# 查看最后100行日志
tail -n 100 logs/server.log
```

### 测试失败
```bash
# 运行测试并显示详细信息
PYTHONPATH=src python -m pytest tests/ -v -s
```

## 支持的图片格式
- JPEG (image/jpeg)
- PNG (image/png)
- WebP (image/webp)

最大支持 10MB 的图片文件。