export type PenpotConfig = { mcpUrl: string; expectedFileId?: string };

export function loadPenpotConfig(env: NodeJS.ProcessEnv = process.env): PenpotConfig {
  const mcpUrl = env.PENPOT_MCP_URL?.trim();
  if (!mcpUrl) throw new Error('CONFIG_ERROR: PENPOT_MCP_URL is required');
  try { new URL(mcpUrl); } catch { throw new Error('CONFIG_ERROR: PENPOT_MCP_URL must be a valid URL'); }
  return { mcpUrl, expectedFileId: env.PENPOT_FILE_ID?.trim() || undefined };
}
