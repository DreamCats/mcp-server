#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ToolSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

// Schema definitions for our encoding/decoding tools
const EncodeArgsSchema = z.object({
  text: z.string().describe("The plain text string to encode"),
});

const DecodeArgsSchema = z.object({
  encodedText: z.string().describe("The base64 encoded string to decode"),
});

const ToolInputSchema = ToolSchema.shape.inputSchema;
type ToolInput = z.infer<typeof ToolInputSchema>;

// Server setup
const server = new Server(
  {
    name: "string-encoding-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// Tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "encode",
        description:
          "Encode a plain text string to base64. This is useful when you need to convert " +
          "text into a format that can be safely transmitted in contexts where binary data " +
          "or special characters might cause issues.",
        inputSchema: zodToJsonSchema(EncodeArgsSchema) as ToolInput,
      },
      {
        name: "decode",
        description:
          "Decode a base64 string back to plain text. Use this when you need to convert " +
          "a base64 encoded string back to its original form. This will throw an error if " +
          "the input is not valid base64.",
        inputSchema: zodToJsonSchema(DecodeArgsSchema) as ToolInput,
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    switch (name) {
      case "encode": {
        const parsed = EncodeArgsSchema.safeParse(args);
        if (!parsed.success) {
          throw new Error(`Invalid arguments for encode: ${parsed.error}`);
        }
        
        const text = parsed.data.text;
        if (!text) {
          throw new Error("Text parameter is required");
        }
        
        const encodedText = Buffer.from(text).toString('base64');
        
        return {
          content: [{ 
            type: "text", 
            text: JSON.stringify({ encodedText }, null, 2) 
          }],
        };
      }

      case "decode": {
        const parsed = DecodeArgsSchema.safeParse(args);
        if (!parsed.success) {
          throw new Error(`Invalid arguments for decode: ${parsed.error}`);
        }
        
        const encodedText = parsed.data.encodedText;
        if (!encodedText) {
          throw new Error("EncodedText parameter is required");
        }
        
        try {
          const decodedText = Buffer.from(encodedText, 'base64').toString('utf-8');
          
          return {
            content: [{ 
              type: "text", 
              text: JSON.stringify({ decodedText }, null, 2) 
            }],
          };
        } catch (error) {
          throw new Error("Invalid base64 string");
        }
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [{ type: "text", text: `Error: ${errorMessage}` }],
      isError: true,
    };
  }
});

// Start server
async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP String Encoding Server running on stdio");
}

runServer().catch((error) => {
  console.error("Fatal error running server:", error);
  process.exit(1);
});
