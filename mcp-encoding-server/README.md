# MCP String Encoding Server

This is a Model Context Protocol (MCP) server that provides utilities for encoding and decoding strings using base64 encoding.

## Features

- **Encode String**: Convert plain text strings to base64 encoded format
- **Decode String**: Convert base64 encoded strings back to plain text

## Installation

```bash
# Clone the repository (or create the file manually)
git clone <repository-url>
cd mcp-string-encoding-server

# Install dependencies
npm install
```

## Usage

The server can be used in two main ways:

### 1. Direct Usage

Run the server directly from the command line:

```bash
./index.js
```

This starts the server using stdio as the transport mechanism, allowing LLMs to interact with it directly.

### 2. As an MCP Tool Server

This server implements the MCP protocol and can be used with any MCP-compatible client or language model.

## Available Tools

The server provides the following tools:

### `encode`

Encode a plain text string to base64.

**Parameters:**

- `text` (string, required): The plain text string to encode

**Example:**

```json
{
  "action": "encode",
  "parameters": {
    "text": "Hello, World!"
  }
}
```

**Response:**

```json
{
  "encodedText": "SGVsbG8sIFdvcmxkIQ=="
}
```

### `decode`

Decode a base64 string back to plain text.

**Parameters:**

- `encodedText` (string, required): The base64 encoded string to decode

**Example:**

```json
{
  "action": "decode",
  "parameters": {
    "encodedText": "SGVsbG8sIFdvcmxkIQ=="
  }
}
```

**Response:**

```json
{
  "decodedText": "Hello, World!"
}
```

## Error Handling

The server provides meaningful error messages for various failure scenarios:

- Invalid base64 strings during decoding
- Missing required parameters
- Invalid parameter types

Example error response:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Invalid base64 string"
    }
  ],
  "isError": true
}
```

## Integration with LLMs

This server can be integrated with Large Language Models using the Model Context Protocol. When an LLM needs to encode or decode strings, it can make requests to this server through the MCP interface.

### Integration Example

```javascript
import { createClient } from "@modelcontextprotocol/client";
import { spawn } from "child_process";

// Start the encoding server
const serverProcess = spawn("./encoding-server.js");

// Create an MCP client connected to the server
const client = createClient({
  transportMode: "stdio",
  process: serverProcess,
});

// Initialize the client
await client.initialize();

// Get available tools
const { tools } = await client.listTools();
console.log(
  "Available tools:",
  tools.map((t) => t.name)
);

// Encode a string
const encodeResult = await client.callTool({
  name: "encode",
  arguments: {
    text: "Hello, World!",
  },
});
console.log("Encoded result:", encodeResult.content[0].text);

// Close the connection
await client.close();
serverProcess.kill();
```

## Development

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn

### Building from Source

```bash
# Install dependencies
npm install

# If using TypeScript
npm run build
```

### Running Tests

```bash
npm test
```

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

This project follows the [Model Context Protocol specification](https://github.com/modelcontextprotocol/spec) and was inspired by the [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem).
