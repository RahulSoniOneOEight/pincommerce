export type PenpotOperation =
  | { kind: 'ensure-page'; repoId: string; name: string }
  | { kind: 'ensure-token-set'; repoId: string; payload: unknown }
  | { kind: 'ensure-component'; repoId: string; payload: unknown }
  | { kind: 'ensure-screen'; repoId: string; payload: unknown }
  | { kind: 'ensure-prototype-link'; repoId: string; payload: unknown };

export type SyncError = { repoId: string; code: string; message: string };
export type SyncResult = { created: number; updated: number; unchanged: number; failed: number; errors: SyncError[] };
export interface PenpotAdapter { apply(operations: PenpotOperation[]): Promise<SyncResult>; }
