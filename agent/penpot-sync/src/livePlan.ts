import type { PenpotOperation } from './adapter.js';
import type { PenpotCapabilities, PenpotRemoteObject } from './mcp/types.js';

export type LivePlanItem = { repoId: string; action: 'create'|'update'|'unchanged'|'orphan'|'unsupported'; operation?: PenpotOperation; current?: PenpotRemoteObject };

function normalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value as Record<string, unknown>).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,normalize(v)]));
  return value;
}

function managedPayload(op: PenpotOperation): unknown {
  return op.kind === 'ensure-page' ? { name: op.name } : op.payload;
}

export function buildLivePlan(desired: PenpotOperation[], current: PenpotRemoteObject[], capabilities: PenpotCapabilities): LivePlanItem[] {
  const byId = new Map(current.filter(x=>x.repoId).map(x=>[x.repoId!, x]));
  const desiredIds = new Set(desired.map(x=>x.repoId));
  const out: LivePlanItem[] = [];
  for (const op of desired) {
    const cur = byId.get(op.repoId);
    if (op.kind === 'ensure-prototype-link' && !capabilities.prototype.supported) { out.push({repoId:op.repoId,action:'unsupported',operation:op,current:cur}); continue; }
    if (!cur) { out.push({repoId:op.repoId,action:'create',operation:op}); continue; }
    const sameKind = cur.kind === op.kind;
    const sameName = op.kind !== 'ensure-page' || cur.name === op.name;
    const samePayload = JSON.stringify(normalize(cur.payload)) === JSON.stringify(normalize(managedPayload(op)));
    out.push({repoId:op.repoId,action:sameKind && sameName && samePayload?'unchanged':'update',operation:op,current:cur});
  }
  for (const cur of current.filter(x=>x.repoId && !desiredIds.has(x.repoId)).sort((a,b)=>a.repoId!.localeCompare(b.repoId!))) out.push({repoId:cur.repoId!,action:'orphan',current:cur});
  return out;
}
