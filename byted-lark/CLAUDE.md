# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a ByteDance Lark MCP (Model Context Protocol) Server that integrates Lark/Feishu services with AI tools. The server provides authentication and API access to Lark knowledge spaces and documents through the MCP framework.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server
```bash
# Basic startup
python main.py

# With custom configuration
python main.py --port 8203 --host localhost --log-level INFO --log-format json

# Environment variables (create .env file)
APP_ID=your_app_id
APP_SECRET=your_app_secret
MCP_PORT=8203
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Code Quality
```bash
# Format code with Black
black src/ main.py demo.py

# Sort imports
isort src/ main.py demo.py

# Run tests (when implemented)
pytest
```

## Architecture

### Core Components

1. **ByteDanceLarkMCPServer** (`src/mcp_server.py`): Main MCP server implementation using FastMCP framework
2. **TenantAccessTokenAuthManager** (`src/auth.py`): Handles Lark API authentication with tenant_access_token
3. **Main Entry Point** (`main.py`): CLI interface and server startup with configurable logging

### Authentication Flow

The server uses tenant_access_token authentication with ByteDance Lark API:
- Authentication endpoint: `https://open.larkoffice.com/open-apis/auth/v3/tenant_access_token/internal`
- Tokens are automatically refreshed when expired
- Requires APP_ID and APP_SECRET from environment variables or CLI arguments

### API Integration

Current API capabilities (based on documentation):
- **Knowledge Space Node Info**: Get metadata about knowledge space nodes
- **Document Content**: Extract raw text content from Lark documents
- **Authentication**: Manage tenant_access_token lifecycle

### Key Dependencies

- **mcp>=1.0.0**: Model Context Protocol framework
- **fastapi>=0.104.0**: Web framework for API endpoints
- **httpx>=0.25.0**: Async HTTP client for API requests
- **structlog>=23.0.0**: Structured logging with JSON/console formats

## Important Notes

### Current State
- Core authentication and server framework are implemented
- Some tool files are empty placeholders (`get_doc.py`, `get_note.py`)
- No test files exist yet
- Demo script (`demo.py`) contains hardcoded credentials - use environment variables in production

### Security Considerations
- Never commit APP_ID or APP_SECRET to version control
- Use environment variables for sensitive configuration
- The demo.py file should not be used in production

### Development Tips
- Server runs on port 8203 by default
- Supports both JSON and console log formats
- Fully async implementation using asyncio
- FastAPI middleware support for CORS and other extensions