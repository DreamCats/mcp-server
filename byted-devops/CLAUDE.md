# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ByteDance MCP (Model Context Protocol) Server** that integrates Claude with ByteDance's internal Bits platform for development task querying. The server provides secure API access with JWT authentication and serves as a bridge between Claude and ByteDance's internal development tools. It allows developers to query development tasks, code changes, and review status directly through Claude.

## Quick Start

### Prerequisites

1. **Python 3.10+** installed on your system
2. **Valid CAS_SESSION cookie** from ByteDance internal systems
3. **Virtual environment** for dependency management

### Setup and Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set CAS_SESSION cookie (required for authentication)
export CAS_SESSION="your_session_cookie_here"
```

### Running the Server

```bash
# Development mode (foreground, colored logs)
python main.py --port 8202 --log-level INFO --log-format console

# Production mode (background, JSON logs)
./startup.sh

# Other management commands
./status.sh      # Check server status
./stop.sh        # Stop the server
./restart.sh     # Restart the server
```

## Architecture Overview

### Core Components

1. **Main Application** ([`main.py`](main.py)):
   - FastAPI application entry point
   - Configures logging with JSON/console formats
   - Manages server lifecycle (startup/shutdown)
   - Handles command-line arguments and environment variables

2. **MCP Server** ([`src/mcp_server.py`](src/mcp_server.py)):
   - Implements FastMCP server for Claude integration
   - Registers and manages MCP tools
   - Handles tool execution and response formatting
   - Orchestrates authentication and API calls

3. **Authentication Manager** ([`src/auth.py`](src/auth.py)):
   - JWTAuthManager class for handling ByteDance authentication
   - Manages CAS_SESSION cookie validation
   - Handles JWT token acquisition and caching
   - Provides automatic token refresh (5-minute buffer)

4. **Bits API Client** ([`src/bits_query_task_changes.py`](src/bits_query_task_changes.py)):
   - BitsQueryForTaskChanges class for querying development tasks
   - Handles API communication with Bits platform
   - Provides comprehensive task information extraction
   - Formats responses for Claude consumption

### Authentication Flow

```
Client Request → MCP Server → JWT Auth Manager → ByteDance Auth API
                    ↓                    ↓
                CAS_SESSION        JWT Token (1-hour expiry)
                    ↓                    ↓
                Bits API ←──── JWT Token ────→ Task Data
```

## Available Tools

### query_bits_task_changes

Queries development tasks from the Bits platform using a development task ID.

**Parameters:**
- `dev_basic_id` (int): Development task base ID (must be positive)

**Returns:**
Comprehensive task information including:
- Task metadata (ID, creator, title, status, creation time)
- Code change details (repository, branches, MR information)
- Code statistics (insertions, deletions)
- Review information (reviewers, status, approval counts)
- Latest commit information

**Example Usage:**
```
query_bits_task_changes(1862036)
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_PORT` | Server listening port | 8202 | No |
| `CAS_SESSION` | ByteDance authentication cookie | - | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO | No |
| `LOG_FORMAT` | Log format (json, console) | json | No |

## API Endpoints

### MCP Protocol Endpoints
- **POST /mcp**: Main MCP protocol endpoint for tool execution
- **GET /**: Server health check and basic info

### Tool Endpoints
- **query_bits_task_changes**: Query Bits platform development tasks
- Built-in MCP discovery and initialization endpoints

## Configuration

### Logging Configuration

The server supports two logging modes:

1. **JSON Format** (Production):
   - Structured JSON logs
   - Machine-readable format
   - Ideal for log aggregation systems

2. **Console Format** (Development):
   - Colored, human-readable output
   - Enhanced debugging visibility
   - Traditional console logging

### Server Configuration

```bash
# Run with custom port
python main.py --port 9000

# Debug mode with verbose logging
python main.py --log-level DEBUG --log-format console

# Production mode
./startup.sh  # Uses environment variables and JSON logging
```

## Development Guidelines

### Code Structure

- **Separation of Concerns**: Each module has distinct responsibilities
- **Async/Await Pattern**: All I/O operations use async programming
- **Type Hints**: Full type annotation support
- **Error Handling**: Comprehensive exception handling with logging

### Adding New Tools

1. Create new query module in `src/` directory
2. Add tool registration in [`src/mcp_server.py`](src/mcp_server.py)
3. Update authentication if needed
4. Add comprehensive documentation and tests

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_auth.py
```

### Code Formatting

```bash
# Format code with black
black src/

# Sort imports
isort src/

# Both commands in sequence
black src/ && isort src/
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   - Verify CAS_SESSION environment variable is set
   - Check if cookie is expired
   - Ensure proper network access to ByteDance internal services

2. **Server Won't Start**:
   - Check port availability (default: 8202)
   - Verify virtual environment is activated
   - Check dependencies are installed correctly

3. **API Timeouts**:
   - Increase timeout values in HTTP client configurations
   - Check network connectivity to Bits platform
   - Verify JWT token is valid

### Debug Commands

```bash
# View real-time logs
tail -f mcp-server.log

# Check server status
./status.sh

# Test API manually
python demo.py

# Verify JWT token acquisition
python -c "from src.auth import JWTAuthManager; print('Auth module loaded')"
```

## Security Considerations

- **Never commit CAS_SESSION cookies** to version control
- **Use HTTPS** for all external API communications
- **Validate all inputs** to prevent injection attacks
- **Rotate JWT tokens** automatically (handled by JWTAuthManager)
- **Monitor logs** for unusual authentication patterns

## Performance Optimization

- **Token caching**: JWT tokens are cached for 55 minutes (5-minute buffer)
- **Async operations**: All I/O operations are non-blocking
- **Connection pooling**: HTTP clients reuse connections
- **Structured logging**: Efficient JSON logging without ANSI codes

## Monitoring and Observability

### Log Structure

All logs use structured format with consistent fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `logger`: Module name
- `event`: Human-readable event description
- Additional context-specific fields

### Key Metrics to Monitor

1. **Authentication success/failure rates**
2. **API response times**
3. **Token refresh frequency**
4. **Error rates by type**
5. **Request throughput**

## Deployment

### Production Deployment

1. **Environment Variables**: Set all required environment variables
2. **Service Management**: Use systemd or similar for process management
3. **Log Rotation**: Configure logrotate for `mcp-server.log`
4. **Monitoring**: Set up log aggregation and monitoring
5. **Backup**: Regular backup of configuration files

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8202

CMD ["python", "main.py", "--port", "8202"]
```

## Contributing

### Development Workflow

1. **Fork** repository
2. **Create feature branch**: `git checkout -b feature/new-tool`
3. **Make changes and add tests**
4. **Format code**: `black src/ && isort src/`
5. **Run tests**: `pytest`
6. **Submit pull request**

### Commit Guidelines

- Use conventional commit format: `feat:`, `fix:`, `docs:`, etc.
- Include clear descriptions of changes
- Reference related issues or tickets
- Update documentation as needed

## Support and Maintenance

### Regular Maintenance Tasks

1. **Dependency updates**: Regular security and feature updates
2. **Log file rotation**: Prevent log file growth
3. **Performance monitoring**: Watch for degradation
4. **Security audits**: Regular security reviews

### Getting Help

1. **Internal Documentation**: Check ByteDance internal wiki
2. **Team Contacts**: Reach out to development team
3. **Bug Reports**: Use internal issue tracking system
4. **Feature Requests**: Submit through internal channels

---

*Last Updated: December 2025*