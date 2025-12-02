# ByteDance MCP Server

A **Model Context Protocol (MCP)** server that bridges Claude with ByteDance's internal Bits platform for development task querying and management.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-1.0+-purple.svg)](https://modelcontextprotocol.io)

## ✨ Features

- **🔐 Secure Authentication**: JWT-based authentication with ByteDance internal systems
- **⚡ Async Performance**: Non-blocking API calls with connection pooling
- **📋 Development Task Query**: Query Bits platform tasks with comprehensive details
- **📊 Rich Response Format**: Structured task information including code changes, reviews, and metadata
- **🛠️ Developer Friendly**: JSON/console logging modes and comprehensive CLI options
- **🔄 Token Management**: Automatic JWT token refresh with caching

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Valid `CAS_SESSION` cookie from ByteDance internal systems
- Access to ByteDance Bits platform

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd byted-devops

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Set required environment variables
export CAS_SESSION="your_cas_session_cookie"
export MCP_PORT=8202  # Optional, defaults to 8202
```

### Running the Server

**Development Mode (Foreground):**
```bash
python main.py --log-format console --log-level INFO
```

**Production Mode (Background):**
```bash
./startup.sh
```

## 📋 Usage

### Query Development Tasks

```python
# Using Claude Code
query_bits_task_changes(1862036)
```

**Response includes:**
- Task metadata (ID, creator, title, status)
- Code change information (repository, branches, MR details)
- Code statistics (insertions, deletions)
- Review information (reviewers, approval status)
- Latest commit details

### Management Commands

```bash
./startup.sh    # Start server in background
./status.sh     # Check server status
./stop.sh       # Stop server
./restart.sh    # Restart server
tail -f mcp-server.log  # View logs
```

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Claude    │────▶│  MCP Server  │────▶│  JWT Auth       │
│   Client    │     │  (FastMCP)   │     │  Manager        │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │                       │
                            ▼                       ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │  Tool        │     │  ByteDance      │
                    │  Execution   │     │  Auth API       │
                    └──────────────┘     └─────────────────┘
                            │                       │
                            └───────────┬───────────┘
                                        ▼
                                ┌──────────────┐
                                │  Bits API    │
                                │  Client      │
                                └──────────────┘
```

## 📁 Project Structure

```
byted-devops/
├── main.py                    # FastAPI entry point
├── src/
│   ├── mcp_server.py         # MCP server implementation
│   ├── auth.py               # JWT authentication
│   └── bits_query_task_changes.py  # Bits API client
├── requirements.txt          # Python dependencies
├── startup.sh               # Server management scripts
├── stop.sh
├── restart.sh
├── status.sh
└── mcp-server.log          # Server logs
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black src/
isort src/

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Adding New Tools

1. Create new module in `src/`
2. Register tool in `src/mcp_server.py`
3. Update authentication if needed
4. Add tests and documentation

## 📊 Configuration

| Environment Variable | Description | Default | Required |
|----------------------|-------------|---------|----------|
| `CAS_SESSION` | ByteDance authentication cookie | - | ✅ |
| `MCP_PORT` | Server listening port | 8202 | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |
| `LOG_FORMAT` | Log format (json/console) | json | ❌ |

## 🔧 API Reference

### Tools

- **`query_bits_task_changes(dev_basic_id: int) -> str`**
  - Query development task details from Bits platform
  - Parameters: `dev_basic_id` (Development task base ID)
  - Returns: Formatted task information with code changes and review status

### Endpoints

- `POST /mcp` - MCP protocol endpoint
- `GET /` - Health check endpoint

## 🐛 Troubleshooting

### Common Issues

**Authentication Failed:**
```bash
# Verify CAS_SESSION is set
echo $CAS_SESSION

# Check server logs for authentication errors
tail -f mcp-server.log | grep auth
```

**Server Won't Start:**
```bash
# Check if port is available
lsof -i :8202

# Verify virtual environment
source .venv/bin/activate
python --version
```

**API Timeouts:**
- Check network connectivity to ByteDance internal services
- Verify JWT token validity in logs
- Increase timeout values if needed

### Debug Mode

```bash
# Run with debug logging
python main.py --log-level DEBUG --log-format console

# Test authentication
python -c "from src.auth import JWTAuthManager; print('Auth OK')"
```

## 🔒 Security

- ✅ JWT tokens automatically expire and refresh
- ✅ CAS_SESSION cookies never logged or exposed
- ✅ All external API calls use HTTPS
- ✅ Input validation and sanitization
- ✅ Structured error handling without information leakage

## 📈 Performance

- **Token Caching**: JWT tokens cached for 55 minutes (5-minute buffer)
- **Async Operations**: Non-blocking I/O for all API calls
- **Connection Pooling**: HTTP connections reused efficiently
- **Structured Logging**: Efficient JSON logging without ANSI codes

## 🐳 Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8202

CMD ["python", "main.py", "--port", "8202"]
```

```bash
# Build and run
docker build -t bytedance-mcp-server .
docker run -p 8202:8202 -e CAS_SESSION="your_cookie" bytedance-mcp-server
```

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive developer documentation
- **[AGENTS.md](AGENTS.md)** - Agent-specific guidelines and project structure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Format code: `black src/ && isort src/`
5. Run tests: `pytest`
6. Submit a pull request

## 📄 License

Internal ByteDance Project - Confidential

## 🆘 Support

For internal support:
- Check ByteDance internal wiki
- Contact the development team
- Use internal issue tracking system

---

**Last Updated:** December 2025
**Version:** 1.0.0