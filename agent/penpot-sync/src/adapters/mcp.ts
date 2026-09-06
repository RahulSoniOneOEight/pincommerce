import type { PenpotAdapter, PenpotOperation, SyncResult } from '../adapter.js';
import { buildLivePlan } from '../livePlan.js';
import type { PenpotMcpGateway } from '../mcp/gateway.js';
import type { PenpotRemoteObject } from '../mcp/types.js';
import type { VisualRenderTarget } from '../visual/renderModel.js';

export class McpPenpotAdapter implements PenpotAdapter {
  constructor(private readonly gateway: PenpotMcpGateway) {}

  async apply(operations: PenpotOperation[], visualTargets: VisualRenderTarget[] = []): Promise<SyncResult> {
    const capabilities = await this.gateway.discover();
    await this.gateway.inspectTarget();
    const current = await this.gateway.listManagedObjects();
    const plan = buildLivePlan(operations, current, capabilities, visualTargets);
    const result: SyncResult = { created: 0, updated: 0, unchanged: 0, failed: 0, errors: [] };
    for (const item of plan) {
      if (!item.operation) continue;
      if (item.action === 'unchanged' || item.action === 'unsupported') { result.unchanged++; continue; }
      if (item.action !== 'create' && item.action !== 'update') continue;
      try {
        let managed: PenpotRemoteObject | undefined = item.current;
        if (item.action === 'create') {
          const created = await this.gateway.create(item.operation);
          managed = {repoId:item.repoId,remoteId:created.remoteId,kind:item.operation.kind,name:'name' in item.operation ? item.operation.name : undefined,payload:'payload' in item.operation ? item.operation.payload : undefined};
          if (item.visualTarget) await this.gateway.renderVisual(item.visualTarget,managed);
          result.created++;
        } else {
          if (item.structuralDrift) await this.gateway.update(item.operation,item.current!);
          if (item.visualDrift && item.visualTarget) await this.gateway.renderVisual(item.visualTarget,item.current!);
          result.updated++;
        }
      } catch (error) {
        result.failed++;
        result.errors.push({ repoId: item.repoId, code: 'WRITE_ERROR', message: error instanceof Error ? error.message : String(error) });
      }
    }
    return result;
  }
}
