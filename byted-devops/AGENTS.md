# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: FastAPI/uvicorn entrypoint; wires the FastMCP app and configures logging.
- `src/mcp_server.py`: Registers MCP tools (currently Bits 任务查询) and glues auth + query logic.
- `src/bits_query_task_changes.py`: Bits API client plus response formatting.
- `src/auth.py`: JWT 获取与缓存，依赖请求头/环境中的 `CAS_SESSION`。
- Shell scripts: `startup.sh`, `stop.sh`, `restart.sh`, `status.sh` 管理本地后台服务；日志输出到 `mcp-server.log`，PID 在 `mcp-server.pid`。
- Dependencies: `requirements.txt`; 推荐本地虚拟环境 `.venv/`（已在仓库根目录）。

## Build, Test, and Development Commands
- 创建/激活虚拟环境并安装依赖：
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- 本地前台运行（控制台日志格式便于调试）：
  ```bash
  python main.py --port 8202 --log-format console
  ```
- 后台运行与管理：
  ```bash
  ./startup.sh    # 启动并写入 mcp-server.pid
  ./status.sh     # 查看端口/日志尾部
  ./stop.sh       # 优雅停止（必要时强杀）
  ./restart.sh    # 停止后再启动
  ```
- 关注 `mcp-server.log` 调试；如需修改端口，使用环境变量 `MCP_PORT`.

## Coding Style & Naming Conventions
- Python 3.10+，4 空格缩进，使用类型注解；模块与函数名保持小写 + 下划线。
- HTTP 客户端用 `httpx.AsyncClient`；避免记录敏感头（`CAS_SESSION`、JWT）并慎用自定义 `Accept-Encoding`，以免压缩流解码失败。
- 日志默认 JSON（生产）；开发可用 `--log-format console`。结构日志使用 `structlog`。
- 格式化与导入排序：
  ```bash
  black .
  isort .
  ```

## Testing Guidelines
- 测试框架：`pytest` + `pytest-asyncio`。测试文件命名 `test_*.py`，按模块分组到 `tests/`。
- 运行全部测试：
  ```bash
  pytest
  ```
- 编写网络相关测试时优先 mock HTTP（避免真实外网调用）；确保异步测试用 `@pytest.mark.asyncio`。

## Commit & Pull Request Guidelines
- 提交信息使用祈使句，前缀可参考 `feat: ...`, `fix: ...`, `chore: ...`；保持简短聚焦，如 `fix: handle non-utf8 bits response`.
- PR 需包含：变更概述、测试结果（列出运行的命令）、关联需求/问题链接。如涉及接口行为变化，附上日志片段或示例响应。

## Security & Configuration Tips
- 认证依赖 `CAS_SESSION`；仅通过请求头或本地环境提供，勿写入仓库或日志。
- 不要在日志/响应中回显 JWT 或 Cookie；必要的调试字段（状态码、长度）替代完整内容。
- 部署前确认端口和日志路径是否符合目标环境要求；长时间运行后定期轮转或清理 `mcp-server.log`。 
