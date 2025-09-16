---
description: Generate default .mcp.json template for local repository
argument-hint: "[--overwrite]"
allowed-tools: ["Write", "Read", "Bash"]
---

# gen_project_mcp

Generate a default `.mcp.json` configuration file for local repositories with pre-configured MCP servers including Lark, Context7, and Fetch services.

## Usage:

`/gen_project_mcp [--overwrite]`

## Process:

1. Check if `.mcp.json` already exists in the current directory
2. If file exists and `--overwrite` flag is not provided, show warning and exit
3. Generate default MCP configuration with the following servers:
   - **lark_mcp**: Lark integration with predefined credentials
   - **context7-mcp**: Context7 HTTP-based MCP service
   - **fetch**: Fetch HTTP-based MCP service
4. Write configuration to `.mcp.json` in the current directory

## Examples:

- Generate MCP configuration in current directory:
  `/gen_project_mcp`

- Overwrite existing MCP configuration:
  `/gen_project_mcp --overwrite`

- Default Template Content:

```json
{
  "mcpServers": {
    "lark_mcp": {
      "command": "lark-mcp",
      "args": [
        "mcp",
        "-a",
        "cli_a8d667668b73900b",
        "-s",
        "FS9N0KX5IFrAnu38ANGQegJpyWeOvEr7"
      ],
      "env": {}
    },
    "context7-mcp": {
      "type": "http",
      "url": "https://mcp.api-inference.modelscope.net/29dd6e59c29640/mcp"
    },
    "fetch": {
      "type": "http",
      "url": "https://mcp.api-inference.modelscope.net/1c8d647f46de47/mcp"
    }
  }
}
```

## Notes:

- The generated configuration includes default credentials that should be updated with your actual API keys
- File will be created in the current working directory
- Use `--overwrite` flag to replace existing configuration
- The template includes three pre-configured MCP servers commonly used in development workflows