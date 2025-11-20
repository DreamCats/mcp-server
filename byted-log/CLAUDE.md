# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ByteDance Log Query MCP Server** - a Model Context Protocol (MCP) server that provides cross-region log query capabilities for ByteDance's internal logging system. It supports both US and Singapore regions with JWT-based authentication.

## Key Architecture

### Core Components
- **FastMCP Framework**: Modern MCP server implementation with async support
- **Multi-region Support**: US (`logservice-tx.tiktok-us.org`) and International (`logservice-sg.tiktok-row.org`) regions
- **JWT Authentication**: Dynamic token management with CAS_SESSION cookie-based auth
- **Session Isolation**: Per-client authentication contexts with proper cleanup

### Directory Structure
```
src/
├── mcp_server.py      # Main MCP server and tool registration
├── auth.py           # JWT authentication manager
├── log_query.py      # Log discovery and query logic
└── __init__.py

tests/                 # Comprehensive test suite with real data
├── test_real_data_workflow.py  # Main test cases
├── conftest.py       # Test configuration and fixtures
└── pytest.ini        # Pytest configuration

main.py               # Server entry point with HTTP setup
startup.sh            # Production service management
status.sh             # Service status checker
stop.sh               # Service stop script
```

## Development Commands

### Running the Server
```bash
# Development mode with console logging
python main.py --host 0.0.0.0 --port 8080 --log-level INFO --log-format console

# Production mode (background service)
./startup.sh    # Start service
./status.sh     # Check status
./stop.sh       # Stop service
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_real_data_workflow.py -v

# Run with custom test runner
python tests/run_tests.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint (if flake8 is available)
flake8 src/ tests/
```

## Environment Configuration

### Required Environment Variables
```bash
# Server configuration
export MCP_HOST=0.0.0.0          # Default: 0.0.0.0
export MCP_PORT=8123               # Default: 8080
export MCP_LOG_LEVEL=INFO          # DEBUG/INFO/WARNING/ERROR
export LOG_FORMAT=json             # json/console

# Authentication (required for log queries)
export CAS_SESSION_US="your-us-session-cookie"      # US region cookie
export CAS_SESSION_I18N="your-international-session-cookie"  # International region cookie
```

### Authentication Priority
1. Region-specific headers: `COOKIE_US`, `COOKIE_I18N`
2. Default cookie headers: `cookie`, `Cookie`
3. Environment variables: `CAS_SESSION_US`, `CAS_SESSION_I18N`

## MCP Tool Usage

The server exposes one main tool: `query_logs_by_logid`

### Parameters
- `logid` (required): Unique log identifier
- `region` (required): Target region (`us` or `i18n`)
- `psm_list` (optional): Comma-separated PSM service filters
- `scan_time_min` (optional): Scan time range in minutes (default: 10)

### Example Usage
```python
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

## Testing Guidelines

### Test Structure
- Tests use **real ByteDance test data** with valid CAS_SESSION cookies
- Mock external HTTP calls to ByteDance services
- Test both success and error scenarios
- Verify authentication flows and region-specific behavior

### Key Test Scenarios
- ✅ Success workflow with real data
- ✅ Authentication error handling
- ✅ Cookie missing scenarios
- ✅ Region-specific cookie priority
- ✅ Multiple PSM service support
- ✅ Exception handling and error responses

### Test Configuration
- Async test support enabled (`asyncio_mode = auto`)
- 30-second timeout for tests
- Coverage reporting with missing lines
- Max 5 failures before stopping

## Important Implementation Notes

### Authentication Flow
1. Extract cookies from request headers (region-specific priority)
2. Fall back to environment variables if headers missing
3. Use cookies to obtain JWT tokens from ByteDance auth service
4. Cache tokens per client session with automatic refresh
5. Clean up authentication resources on client disconnect

### Error Handling
- Detailed error messages in Chinese with troubleshooting guidance
- Graceful handling of network timeouts and auth failures
- Proper HTTP status codes and error categorization
- Structured logging for debugging

### Performance Considerations
- Async/await throughout for high concurrency
- Concurrent queries across multiple regions
- JWT token caching to avoid repeated auth calls
- Proper resource cleanup to prevent memory leaks

### Security Notes
- Never commit CAS_SESSION cookies to version control
- Session isolation prevents cross-client data leakage
- JWT tokens are client-specific and time-limited
- Proper cleanup of authentication resources