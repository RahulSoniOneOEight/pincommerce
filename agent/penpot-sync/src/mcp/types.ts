export type McpTool = { name: string; description?: string; inputSchema?: unknown };

export interface McpTransport {
  connect(): Promise<void>;
  listTools(): Promise<McpTool[]>;
  callTool(name: string, args: Record<string, unknown>): Promise<unknown>;
  close(): Promise<void>;
}

export type PenpotCapabilities = {
  read: { supported: boolean; tool?: string };
  create: { supported: boolean; tool?: string };
  update: { supported: boolean; tool?: string };
  prototype: { supported: boolean; tool?: string };
};

export type PenpotTarget = { fileId?: string; pageId?: string; fileName?: string; pageName?: string };
export type PenpotRemoteObject = { repoId?: string; remoteId: string; kind: string; name?: string; payload?: unknown };
