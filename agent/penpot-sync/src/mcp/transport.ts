import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import type { PenpotConfig } from '../config.js';
import { redactText, redactUrl } from '../redact.js';
import type { McpTool, McpTransport } from './types.js';

export class RemoteMcpTransport implements McpTransport {
  private client?: Client;
  private transport?: StreamableHTTPClientTransport;

  constructor(private readonly config: PenpotConfig) {}

  async connect(): Promise<void> {
    try {
      this.client = new Client({ name: 'pincommerce-penpot-sync', version: '0.1.0' });
      this.transport = new StreamableHTTPClientTransport(new URL(this.config.mcpUrl));
      await this.client.connect(this.transport);
    } catch (error) {
      const message = redactText(error instanceof Error ? error.message : String(error));
      throw new Error(`MCP_CONNECT_ERROR: ${redactUrl(this.config.mcpUrl)} ${message}`);
    }
  }

  async listTools(): Promise<McpTool[]> {
    if (!this.client) throw new Error('MCP_CONNECT_ERROR: client is not connected');
    const result = await this.client.listTools();
    return result.tools.map(tool => ({ name: tool.name, description: tool.description, inputSchema: tool.inputSchema }));
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    if (!this.client) throw new Error('MCP_CONNECT_ERROR: client is not connected');
    return this.client.callTool({ name, arguments: args });
  }

  async close(): Promise<void> {
    if (this.client) await this.client.close();
    this.client = undefined;
    this.transport = undefined;
  }
}
