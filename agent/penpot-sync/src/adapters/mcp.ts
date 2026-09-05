import type { PenpotAdapter, PenpotOperation, SyncResult } from '../adapter.js';
import { buildLivePlan } from '../livePlan.js';
import type { PenpotMcpGateway } from '../mcp/gateway.js';

export class McpPenpotAdapter implements PenpotAdapter {
  constructor(private readonly gateway: PenpotMcpGateway) {}

  async apply(operations: PenpotOperation[]): Promise<SyncResult> {
    const capabilities = await this.gateway.discover();
    await this.gateway.inspectTarget();
    const current = await this.gateway.listManagedObjects();
    const plan = buildLivePlan(operations, current, capabilities);
    const result: SyncResult = { created: 0, updated: 0, unchanged: 0, failed: 0, errors: [] };
    for (const item of plan) {
      if (!item.operation) continue;
      if (item.action === 'unchanged' || item.action === 'unsupported') { result.unchanged++; continue; }
      if (item.action !== 'create' && item.action !== 'update') continue;
      try {
        if (item.action === 'create') { await this.gateway.create(item.operation); result.created++; }
        else { await this.gateway.update(item.operation, item.current!); result.updated++; }
      } catch (error) {
        result.failed++;
        result.errors.push({ repoId: item.repoId, code: 'WRITE_ERROR', message: error instanceof Error ? error.message : String(error) });
      }
    }
    return result;
  }
}
