# 股票 MCP 服务使用指南

## 快速启动

### 1. 启动服务

```bash
# 前台运行（推荐用于开发和调试）
./start.sh

# 后台运行（推荐用于生产环境）
./start.sh -d

# 指定端口启动
./start.sh -p 8125

# 后台运行并指定端口
./start.sh -d -p 8125
```

### 2. 停止服务

```bash
# 正常停止服务
./stop.sh

# 强制停止服务
./stop.sh -f

# 查看服务状态
./stop.sh -s

# 查看最近日志
./stop.sh -l
```

## 详细使用说明

### 启动脚本 (start.sh)

#### 功能特性
- ✅ 自动检查 Python 环境和依赖包
- ✅ 自动安装缺失的依赖包
- ✅ 支持前台和后台运行模式
- ✅ 自定义端口和主机地址
- ✅ 进程管理和日志记录
- ✅ 防止重复启动

#### 命令选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-p, --port` | 指定端口号 | 8124 |
| `-h, --host` | 指定主机地址 | localhost |
| `-d, --daemon` | 后台运行模式 | 前台运行 |
| `-f, --foreground` | 前台运行模式 | - |
| `--help` | 显示帮助信息 | - |

#### 使用示例

```bash
# 基本启动
./start.sh

# 自定义端口
./start.sh --port 8125

# 后台运行
./start.sh --daemon

# 后台运行 + 自定义端口
./start.sh -d -p 8125

# 绑定所有网络接口
./start.sh --host 0.0.0.0
```

### 停止脚本 (stop.sh)

#### 功能特性
- ✅ 优雅停止服务进程
- ✅ 强制停止选项
- ✅ 服务状态检查
- ✅ 日志查看功能
- ✅ 文件清理功能

#### 命令选项

| 选项 | 说明 |
|------|------|
| `-f, --force` | 强制停止服务 |
| `-s, --status` | 显示服务状态 |
| `-l, --logs` | 显示最近的日志 |
| `--clean` | 清理日志和PID文件 |
| `--help` | 显示帮助信息 |

#### 使用示例

```bash
# 正常停止
./stop.sh

# 强制停止
./stop.sh --force

# 查看状态
./stop.sh --status

# 查看日志
./stop.sh --logs

# 清理文件
./stop.sh --clean
```

## 服务管理

### 文件说明

| 文件 | 说明 |
|------|------|
| `stock_mcp.pid` | 进程ID文件，记录服务进程号 |
| `stock_mcp.log` | 服务日志文件，记录运行日志 |

### 常用操作

#### 查看服务状态
```bash
./stop.sh -s
```

#### 查看实时日志
```bash
tail -f stock_mcp.log
```

#### 重启服务
```bash
./stop.sh && ./start.sh -d
```

#### 查看最近错误
```bash
./stop.sh -l | grep -i error
```

## 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 错误信息：Address already in use
# 解决方案：
./start.sh -p 8125  # 使用其他端口
```

#### 2. 依赖包缺失
```bash
# 错误信息：ModuleNotFoundError
# 解决方案：脚本会自动安装，或手动安装
pip install -r requirements.txt
```

#### 3. 权限问题
```bash
# 错误信息：Permission denied
# 解决方案：
chmod +x start.sh stop.sh
```

#### 4. 服务无法停止
```bash
# 使用强制停止
./stop.sh -f

# 或清理文件后重新启动
./stop.sh --clean
./start.sh -d
```

### 日志分析

#### 查看启动日志
```bash
head -n 20 stock_mcp.log
```

#### 查看错误日志
```bash
grep -i "error\|exception\|failed" stock_mcp.log
```

#### 查看最近活动
```bash
tail -n 50 stock_mcp.log
```

## 开发模式

### 前台运行（推荐开发时使用）
```bash
./start.sh
# 优点：可以直接看到输出，Ctrl+C 停止
# 缺点：终端关闭服务就停止
```

### 后台运行（推荐生产环境）
```bash
./start.sh -d
# 优点：服务在后台运行，不受终端影响
# 缺点：需要查看日志文件了解运行状态
```

## 生产环境建议

1. **使用后台模式**：`./start.sh -d`
2. **定期查看日志**：`./stop.sh -l`
3. **监控服务状态**：`./stop.sh -s`
4. **设置日志轮转**：防止日志文件过大
5. **配置开机自启**：可以添加到系统服务

## 系统集成

### 添加到系统服务 (systemd)

创建服务文件 `/etc/systemd/system/stock-mcp.service`：

```ini
[Unit]
Description=Stock MCP Server
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/path/to/stock
ExecStart=/path/to/stock/start.sh -d
ExecStop=/path/to/stock/stop.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable stock-mcp
sudo systemctl start stock-mcp
```

## MCP 客户端测试

### 测试 MCP 连接

```bash
# 1. 启动服务
./start.sh -d

# 2. 运行 MCP 客户端测试
python test_mcp_client.py

# 3. 查看服务状态
./stop.sh -s
```

### Claude Desktop 集成

1. 复制 `claude_desktop_config.json` 的内容
2. 修改路径为你的实际项目路径
3. 添加到 Claude Desktop 配置文件中
4. 重启 Claude Desktop

### 自定义 MCP 客户端

参考 `test_mcp_client.py` 中的示例代码，可以创建自己的 MCP 客户端应用。

---

**注意**：首次使用前请确保已安装 Python 3.8+ 和相关依赖包。脚本会自动检查并安装缺失的依赖。
