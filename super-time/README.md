# SuperTime MCP 服务

基于 fastmcp 的灵活时间获取服务，支持 streamable HTTP 协议。

## 功能特性

✅ **基础时间获取**
- 获取当前时间的格式化字符串
- 获取当前时间戳

✅ **时间范围处理**
- 获取指定时间范围内的时间戳
- 获取指定时间范围内的时间列表（支持流式返回）

✅ **时区处理**
- 获取指定时区的时间
- 获取指定时区的时间戳

✅ **相对时间处理**
- 获取最近N分钟前的时间
- 获取最近N分钟前的时间戳

✅ **完整时间信息**
- 获取包含多种格式的完整时间信息
- 支持中文星期显示

## 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行安装脚本
./install.sh
```

### 2. 启动服务

```bash
python start.py
```

### 3. 运行测试

```bash
pytest tests/ -v
```

## API 说明

### 基础时间获取

#### `get_current_time`
获取当前时间的格式化字符串

**参数：**
- `format_str` (可选): 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

**返回：** 格式化的时间字符串

#### `get_current_timestamp`
获取当前时间戳（秒级）

**返回：** 当前时间戳（秒）

### 时间范围处理

#### `get_timestamp_range`
获取指定时间范围内的时间戳

**参数：**
- `start_time`: 开始时间字符串
- `end_time`: 结束时间字符串
- `format_str` (可选): 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

**返回：** 包含开始和结束时间戳的字典

#### `get_time_range`
获取指定时间范围内的时间列表（流式返回）

**参数：**
- `start_time`: 开始时间字符串
- `end_time`: 结束时间字符串
- `format_str` (可选): 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"
- `interval_seconds` (可选): 时间间隔（秒），默认为60秒

**返回：** 流式返回格式化的时间字符串

### 时区处理

#### `get_timezone_time`
获取指定时区的时间

**参数：**
- `timezone` (可选): 时区名称，默认为 "Asia/Shanghai"
- `format_str` (可选): 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

**返回：** 指定时区的格式化时间字符串

#### `get_timezone_timestamp`
获取指定时区的时间戳

**参数：**
- `timezone` (可选): 时区名称，默认为 "Asia/Shanghai"

**返回：** 指定时区的当前时间戳（秒）

### 相对时间处理

#### `get_recent_time`
获取最近N分钟前的时间

**参数：**
- `minutes` (可选): 分钟数，默认为10分钟
- `format_str` (可选): 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

**返回：** 最近N分钟前的时间字符串

#### `get_recent_timestamp`
获取最近N分钟前的时间戳

**参数：**
- `minutes` (可选): 分钟数，默认为10分钟

**返回：** 最近N分钟前的时间戳（秒）

### 完整时间信息

#### `get_time_info`
获取完整的时间信息（包含多个格式）

**参数：**
- `timezone` (可选): 时区名称，默认为 "Asia/Shanghai"
- `format_str` (可选): 时间格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

**返回：** 包含多种时间格式的信息字典

## 使用示例

### 基础使用

```python
# 获取当前时间
current_time = await get_current_time()
print(f"当前时间: {current_time}")

# 获取当前时间戳
timestamp = await get_current_timestamp()
print(f"当前时间戳: {timestamp}")
```

### 时区处理

```python
# 获取东八区时间
shanghai_time = await get_timezone_time("Asia/Shanghai")
print(f"上海时间: {shanghai_time}")

# 获取UTC时间
utc_time = await get_timezone_time("UTC")
print(f"UTC时间: {utc_time}")
```

### 时间范围

```python
# 获取时间戳范围
range_info = await get_timestamp_range(
    "2023-01-01 00:00:00",
    "2023-01-01 01:00:00"
)
print(f"时间戳范围: {range_info}")

# 流式获取时间列表
async for time_str in get_time_range(
    "2023-01-01 00:00:00",
    "2023-01-01 00:05:00",
    interval_seconds=60
):
    print(f"时间: {time_str}")
```

### 相对时间

```python
# 获取30分钟前的时间
recent_time = await get_recent_time(minutes=30)
print(f"30分钟前: {recent_time}")

# 获取完整时间信息
time_info = await get_time_info("Asia/Shanghai")
print(f"完整时间信息: {time_info}")
```

## 时间格式说明

支持标准 Python datetime 格式字符串：

- `%Y`: 4位年份（如：2023）
- `%m`: 2位月份（01-12）
- `%d`: 2位日期（01-31）
- `%H`: 24小时制小时（00-23）
- `%M`: 分钟（00-59）
- `%S`: 秒（00-59）

### 常用格式示例

- `"%Y-%m-%d %H:%M:%S"` → "2023-01-01 12:30:45"
- `"%Y年%m月%d日 %H时%M分%S秒"` → "2023年01月01日 12时30分45秒"
- `"%Y-%m-%d"` → "2023-01-01"
- `"%H:%M:%S"` → "12:30:45"

## 支持的时区

支持所有标准的 IANA 时区名称：

- `"Asia/Shanghai"` - 中国标准时间（东八区）
- `"Asia/Tokyo"` - 日本标准时间
- `"America/New_York"` - 美国东部时间
- `"Europe/London"` - 英国时间
- `"UTC"` - 协调世界时

## 开发说明

### 项目结构

```
super-time/
├── src/
│   └── super_time/
│       └── __init__.py    # 主要MCP服务代码
├── tests/
│   └── test_super_time.py # 测试用例
├── pyproject.toml         # 项目配置
├── start.py              # 启动脚本
├── install.sh            # 安装脚本
└── README.md             # 使用说明
```

### 添加新功能

1. 在 `src/super_time/__init__.py` 中添加新的工具函数
2. 使用 `@mcp.tool()` 装饰器注册新功能
3. 在 `tests/test_super_time.py` 中添加对应的测试用例
4. 更新 README.md 文档

## 许可证

MIT License