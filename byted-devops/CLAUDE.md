# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ByteDance MCP (Model Context Protocol) Server** that integrates Claude with ByteDance's internal Bits platform for development task querying. The server provides secure API access with JWT authentication and serves as a bridge between Claude and ByteDance's internal development tools.

## Essential Commands

### Server Management

```bash
# Start the MCP server (background mode)
./startup.sh

# Stop the server
./stop.sh

# Restart the server
./restart.sh

# Check server status
./status.sh

# View logs in real-time
tail -f mcp-server.log
```

### Development Commands

```bash
# Install dependencies (ensure virtual environment is activated)
pip install -r requirements.txt

# Run the server directly (foreground mode)
python main.py --port 8202 --log-level INFO --log-format console

# Run tests
pytest

# Format code
black src/
isort src/

# Test API manually
python demo.py
```

## Architecture Overview

### Core Components

1. **MCP Server** (`src/mcp_server.py`): Main FastAPI-based MCP server that registers tools and handles requests
2. **Authentication** (`src/auth.py`): JWTAuthManager handles secure authentication with ByteDance APIs using CAS_SESSION cookies
3. **Bits API Integration** (`src/bits_query_task_changes.py`): Queries development tasks from ByteDance Bits platform

### Authentication Flow

```
Client Request → MCP Server → JWT Auth Manager → ByteDance API
                    ↓
              Validates CAS_SESSION cookie and obtains JWT token
```

### Key Environment Variables

- `MCP_PORT`: Server port (default: 8202)
- `CAS_SESSION`: Authentication cookie for ByteDance internal systems

### API Endpoints

- **MCP Tools**: `query_bits_task_changes` - Queries development tasks from Bits platform
- **Server Health**: Standard FastAPI endpoints for health checks

## Important Notes

- The server requires a valid `CAS_SESSION` cookie environment variable for authentication
- All API calls are logged with structured logging (JSON format in production, colored console in development)
- The server runs on localhost:8202 by default
- Process management is handled via PID files for clean startup/shutdown
- Recent logs show successful API queries indicating active functionality
