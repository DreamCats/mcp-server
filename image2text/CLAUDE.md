# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an image2text MCP (Model Context Protocol) server project that provides image-to-text conversion capabilities for Claude Code tools. The project uses company APIs instead of native APIs for better cost-effectiveness and compatibility.

## Key Requirements

- **Language**: Python with MCP SDK
- **Protocol**: HTTP-based MCP server
- **Port**: 8201
- **API Protocol**: OpenAI-compatible for image processing
- **Comments**: All methods must have detailed Chinese comments
- **Testing**: Unit tests required for all new features
- **Architecture**: Modular, maintainable, and iterative design

## Project Structure

```
/Users/bytedance/Demo/mcp/image2text/
├── .venv/                    # Python virtual environment (activated)
├── .claude/                  # Claude configuration
│   └── settings.local.json   # Enabled MCP servers config
├── .mcp.json                 # MCP servers configuration
└── 诉求.md                   # Project requirements (Chinese)
```

## Development Commands

Since this is a new project without existing implementation, you'll need to:

1. **Install dependencies** (when requirements are defined):
   ```bash
   pip install mcp[cli] fastapi uvicorn httpx
   ```

2. **Run the MCP server** (once implemented):
   ```bash
   python image2text_server.py --port 8201
   ```

3. **Run tests** (once test framework is set up):
   ```bash
   python -m pytest tests/
   ```

## Architecture Guidelines

### MCP Server Implementation
- Use `FastMCP` from `mcp.server.fastmcp`
- Implement HTTP transport with streaming support
- Configure JSON response and stateless HTTP modes as needed

### Image Processing Tool
- Create tool function decorated with `@mcp.tool()`
- Accept image input and configuration via function parameters
- Use OpenAI-compatible API protocol for text extraction
- Support configuration via HTTP headers (base URL, API key, model ID)

### Configuration Management
- API parameters passed via HTTP headers: `base_url`, `apikey`, `modelid`
- Environment-based configuration for development/production
- Extensible design for future API providers

## Code Standards

- **Comments**: All public methods and complex logic must have Chinese comments
- **Error Handling**: Proper exception handling with user-friendly messages
- **Modularity**: Separate concerns into different modules (config, utils, main)
- **Testing**: Write unit tests for each component before implementation

## MCP Configuration

The `.mcp.json` file contains various MCP server configurations including:
- Lark MCP for Feishu/Lark integration
- Context7 MCP for documentation
- GitHub MCP for repository operations
- ModelScope Image Generation MCP
- Time and Maps MCP servers

When implementing, ensure compatibility with existing MCP server ecosystem.