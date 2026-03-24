#!/usr/bin/env node
'use strict';

const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');

const { buildToolDefinitions, toErrorResult } = require('./lib/tools');

class ReverseNetworkMCPServer {
  constructor() {
    this._keepAliveTimer = null;
    this._server = new McpServer({
      name: 'reverse-network-mcp-server',
      version: '0.1.0',
    });
    this._registerTools();
  }

  _registerTools() {
    for (const tool of buildToolDefinitions()) {
      this._server.registerTool(
        tool.name,
        {
          description: tool.description,
          inputSchema: tool.inputShape,
        },
        async args => {
          try {
            return await tool.handler(args || {});
          } catch (error) {
            return toErrorResult(error);
          }
        },
      );
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this._server.connect(transport);
    process.stdin.resume();
    this._keepAliveTimer = setInterval(() => {}, 60 * 1000);
  }
}

async function main() {
  const server = new ReverseNetworkMCPServer();
  await server.run();
}

process.on('SIGINT', () => process.exit(0));
process.on('SIGTERM', () => process.exit(0));

main().catch(error => {
  process.stderr.write(`${error instanceof Error ? error.stack || error.message : String(error)}\n`);
  process.exit(1);
});
