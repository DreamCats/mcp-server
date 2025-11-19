# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **byted-api MCP (Model Context Protocol) tool** project that integrates with ByteDance's internal service discovery system. The tool provides JWT-based authentication and PSM (Product, Subsys, Module) service lookup capabilities.

## Essential Development Commands

### Environment Setup
```bash
# Activate virtual environment (required before any operations)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server
```bash
# Production startup (recommended - background mode with logging)
./startup.sh

# Development mode (foreground)
python main.py --port 8123

# Check server status
./status.sh

# Stop server
./stop.sh
```

### Testing Commands
```bash
# Run comprehensive integration tests
python tests/test_comprehensive.py

# Test specific modules
python tests/test_mcp.py                    # Basic MCP functionality
python tests/test_cluster_discovery.py      # Cluster discovery
python tests/test_instance_discovery.py     # Instance address discovery
python tests/test_rpc_simulation.py         # RPC request simulation
python tests/test_error_handling.py         # Error handling
python tests/test_multi_region_auth.py      # Multi-region authentication

# Test authentication flow
python test_mcp.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/
```

## High-Level Architecture

### Core Service Flow
1. **Authentication** → **Service Discovery** → **Cluster Discovery** → **Instance Discovery** → **RPC Simulation**
2. All API calls require valid JWT tokens in `x-jwt-token` header
3. Multi-region concurrent queries for reliability and performance

### Key Components Integration

```
main.py (entry point)
    ↓
mcp_server.py (FastMCP framework)
    ↓
auth.py ←→ service_discovery.py ←→ cluster_discovery.py ←→ instance_discovery.py ←→ rpc_simulation.py
    ↓
ByteDance Internal APIs (Neptune, TikTok ROW)
```

### Critical Implementation Details

**Multi-Region Architecture:**
- CN Region: `https://ms-neptune.byted.org/api/neptune/ms/service/search`
- US Region: `https://ms-neptune.tiktok-us.org/api/neptune/ms/service/search`
- Concurrent queries to both regions, returns first valid result

**Authentication Flow:**
- JWT tokens retrieved from `https://cloud.bytedance.net/auth/api/v1/jwt`
- Uses `CAS_SESSION` cookie from environment
- Multi-region cookie support: `CAS_SESSION_cn`, `CAS_SESSION_i18n`, `CAS_SESSION_us`

**API Integration Points:**
- **Neptune Service Registry**: PSM service discovery (dual-region)
- **TikTok ROW API**: Cluster/instance discovery and RPC simulation
- **Authentication Service**: JWT token management

### MCP Tools Architecture

The server exposes 8 MCP tools through FastMCP framework:

1. `search_psm_service` - Concurrent PSM search across regions
2. `check_jwt_status` - JWT token validation and status
3. `list_available_regions` - Available region configuration
4. `search_multiple_services` - Batch PSM service search
5. `discover_clusters` - TikTok ROW cluster discovery
6. `discover_instances` - Instance address resolution
7. `simulate_rpc_request` - RPC request simulation
8. `query_logs_by_logid` - Log query for US-TTP region

### Error Handling Strategy

- **JWT Invalid**: Automatic retry with region-specific cookies
- **Service Not Found**: Comprehensive search across both regions
- **Network Issues**: Timeout handling with user-friendly messages
- **Authentication Failures**: Clear guidance on cookie configuration

### Production Deployment

**Startup Script Features:**
- Background process management with PID tracking
- Automatic virtual environment activation
- Comprehensive logging to `mcp-server.log`
- Port configuration via `MCP_PORT` environment variable
- Process lifecycle management (start/stop/status)

**Environment Variables:**
```bash
CAS_SESSION="your_cookie_value"     # Required: Main authentication cookie
CAS_SESSION_cn="..."                # Optional: CN region specific
CAS_SESSION_i18n="..."              # Optional: i18n region specific
CAS_SESSION_us="..."                # Optional: US region specific
MCP_PORT="8123"                     # Optional: Server port (default: 8123)
```

### Testing Strategy

**Multi-layered testing approach:**
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Cross-component workflow testing
3. **Multi-region Tests**: Authentication and service discovery across regions
4. **Error Handling Tests**: Failure scenario validation
5. **End-to-end Tests**: Complete workflow validation

**Test Execution Pattern:**
- Always activate virtual environment first
- Run comprehensive tests before commits
- Use specific test files for targeted debugging
- Validate multi-region functionality for production readiness

### Security Considerations

- JWT tokens are environment-specific and must be kept secure
- All API calls use HTTPS with proper certificate validation
- Cookie-based authentication requires valid ByteDance session
- No credentials are logged or exposed in responses
- Regional authentication isolation for security boundaries