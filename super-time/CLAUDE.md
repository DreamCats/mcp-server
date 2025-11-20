# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperTime is a Model Context Protocol (MCP) server built with FastMCP that provides flexible time-related functionality through HTTP streaming protocol on port 8201.

## Key Commands

### Development Setup
```bash
# Install dependencies (uses UV package manager)
./install.sh

# Activate virtual environment
source .venv/bin/activate
```

### Service Management
```bash
# Start service (production, HTTP on port 8201)
./start.sh

# Stop service
./stop.sh

# Check service status
./status.sh

# Restart service
./restart.sh

# Development mode (stdio protocol)
python start.py
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_super_time.py::test_function_name -v
```

## Architecture

### Core Structure
- **`src/super_time/__init__.py`**: MCP server with tool decorators exposing 9 time functions
- **`src/super_time/core.py`**: Core time processing functions (all async)
- **`start.py`**: Development entry point using stdio protocol
- **Shell scripts**: Production service management with HTTP streaming

### MCP Tool Architecture
All tools follow the pattern:
1. Core function in `core.py` (async)
2. MCP tool wrapper in `__init__.py` with `@mcp.tool()` decorator
3. Tool names map directly to function names (e.g., `current_time` → `get_current_time()`)

### Service Configuration
- **Protocol**: streamable-http (production), stdio (development)
- **Port**: 8201
- **Host**: 0.0.0.0
- **PID file**: `supertime_mcp.pid` (project root)
- **Log file**: `supertime_mcp.log` (project root)

### Key Functions
1. **Basic time**: `current_time`, `current_timestamp`
2. **Time ranges**: `timestamp_range`, `time_range` (streaming)
3. **Timezone**: `timezone_time`, `timezone_timestamp`
4. **Relative time**: `recent_time`, `recent_timestamp`
5. **Complete info**: `time_info`

### Testing Patterns
- All functions are async and tested with `@pytest.mark.asyncio`
- Tests validate both functionality and error handling
- Streaming tests verify async generator behavior
- Timezone validation tests ensure proper error messages

### Error Handling
- Timezone validation with descriptive Chinese error messages
- Graceful handling of invalid date formats
- Proper async error propagation through MCP tools