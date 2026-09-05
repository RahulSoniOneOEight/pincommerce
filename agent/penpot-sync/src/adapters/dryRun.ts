import type { PenpotAdapter, PenpotOperation, SyncResult } from '../adapter.js';

export class DryRunAdapter implements PenpotAdapter {
  async apply(operations: PenpotOperation[]): Promise<SyncResult> {
    return { created: 0, updated: 0, unchanged: operations.length, failed: 0, errors: [] };
  }
}
