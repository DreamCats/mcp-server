# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **byted-api MCP (Model Context Protocol) tool** project that integrates with ByteDance's internal service discovery system. The tool provides JWT-based authentication and PSM (Product, Subsys, Module) service lookup capabilities.

## Architecture

### Core Components

1. **JWT Authentication Layer** (`test.py:3-20`)
   - Retrieves JWT tokens from ByteDance auth service
   - Uses `CAS_SESSION` cookie for authentication
   - Base URL: `https://cloud.bytedance.net/auth/api/v1/jwt`

2. **PSM Service Discovery** (`test.py:26-36`)
   - Searches ByteDance Neptune service registry
   - Requires JWT token in `x-jwt-token` header
   - **Concurrent Requests**: Must query both regions simultaneously:
     - `https://ms-neptune.byted.org/api/neptune/ms/service/search`
     - `https://ms-neptune.tiktok-us.org/api/neptune/ms/service/search`
   - Returns result from whichever endpoint has matching PSM for the keyword

3. **Cluster Discovery**
   - Queries TikTok Row API to find clusters associated with a PSM
   - Requires JWT token in `x-jwt-token` header
   - Base URL: `https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/plane/clusters`
   - Parameters: `psm`, `test_plane=1`, `env=prod`
   - Returns cluster information including zone, IDC, and online status

4. **Instance Address Discovery**
   - Queries TikTok Row API to find machine instance addresses for a specific cluster
   - Requires JWT token in `x-jwt-token` header
   - Base URL: `https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/addrs`
   - Parameters: `psm`, `env=prod`, `zone`, `idc`, `cluster`
   - Returns array of instance addresses in format `[ip]:port`

5. **i18n RPC Request Simulation**
   - Simulates RPC requests to i18n services using discovered instance addresses
   - Requires JWT token in `x-jwt-token` header
   - Base URL: `https://cloud.tiktok-row.net/api/v1/explorer/explorer/v5/rpc_request`
   - Method: POST with comprehensive request body including:
     - `address`: Target instance address (required)
     - `cluster`: Cluster name (required, defaults to "default")
     - `env`: Environment (required, defaults to "prod")
     - `zone`: Geographic zone (required)
     - `idc`: Data center identifier (required)
     - `psm`: Service name (required)
     - `func_name`: RPC method name (required)
     - `req_body`: JSON request body (required)
     - Additional parameters: `idl_source`, `idl_version`, `online`, `rpc_context`, `source`, `request_timeout`
   - Returns RPC response with `resp_body`, performance metrics, and debug information

6. **MCP Server Framework**
   - Uses FastMCP Python SDK for streamable HTTP transport
   - Follows server-client-transport triad architecture
   - Supports both JSON and SSE streaming responses

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install MCP dependencies (when requirements.txt is available)
uv pip install mcp fastapi uvicorn httpx
```

### Testing Authentication Flow
```bash
# Test JWT token retrieval and PSM search
python test.py
```

### Running MCP Server
```bash
# Start streamable HTTP server (based on weather example from 诉求.md:114-120)
python main.py --port 8123
```

## Key Implementation Patterns

### Authentication Headers
```python
jwt_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": f"CAS_SESSION={cookie_value}"
}
```

### Cluster Discovery Headers
```python
cluster_header = {
    "accept": "application/json, text/plain, */*",
    "x-jwt-token": jwt_token
}
```

### MCP Tool Structure
```python
from mcp.server.fastmcp import FastMCP
import asyncio
import httpx

mcp = FastMCP(name="byted-api", json_response=False, stateless_http=False)

@mcp.tool()
async def get_service_info(keyword: str) -> str:
    """Get service information from Neptune registry with concurrent region queries.

    Args:
        keyword: Service keyword to search for

    Returns:
        Service information from the region that has matching PSM
    """
    # Concurrent requests to both regions
    # Implementation should query both URLs and return the one with matching PSM
    return formatted_result

@mcp.tool()
async def get_clusters(psm: str) -> str:
    """Get cluster information for a given PSM from TikTok Row API.

    Args:
        psm: Product, Subsys, Module identifier

    Returns:
        Cluster information including zone, IDC, and online status
    """
    # Query cluster information using psm
    # Return formatted cluster details
    return formatted_result

@mcp.tool()
async def get_instance_addresses(psm: str, zone: str, idc: str, cluster: str) -> str:
    """Get instance addresses for a specific cluster from TikTok Row API.

    Args:
        psm: Product, Subsys, Module identifier
        zone: Geographic zone identifier
        idc: Data center identifier
        cluster: Cluster name

    Returns:
        Array of instance addresses in format [ip]:port
    """
    # Query instance addresses using cluster parameters
    # Return formatted address list
    return formatted_result

@mcp.tool()
async def simulate_rpc_request(psm: str, address: str, func_name: str, req_body: str,
                               zone: str, idc: str, cluster: str = "default", env: str = "prod") -> str:
    """Simulate RPC request to i18n service using discovered instance address.

    Args:
        psm: Product, Subsys, Module identifier
        address: Target instance address in format [ip]:port
        func_name: RPC method name to call
        req_body: JSON string request body
        zone: Geographic zone identifier
        idc: Data center identifier
        cluster: Cluster name (defaults to "default")
        env: Environment (defaults to "prod")

    Returns:
        RPC response including resp_body, performance metrics, and debug information
    """
    # Simulate RPC request with comprehensive request body
    # Return formatted response with performance metrics and debug info
    return formatted_result
```

## Configuration Files

- **`.mcp.json`**: MCP server configurations for Lark, Context7, and Fetch services
- **`.claude/settings.local.json`**: Claude-specific settings
- **`.claude/agents/mcp-development-specialist.md`**: MCP development guidelines

## External Dependencies

- **ByteDance Internal APIs**: Authentication and service discovery
- **Neptune Service Registry**: PSM service lookup (dual-region: byted.org and tiktok-us.org)
- **TikTok Row APIs**: Cluster and instance address discovery
- **FastMCP SDK**: MCP server implementation framework
- **httpx**: For concurrent HTTP requests to multiple regions

## Security Considerations

- JWT tokens are retrieved from environment-specific cookie values
- Service discovery requires valid JWT authentication
- All API calls should include proper error handling and timeouts