import type { PenpotOperation } from './adapter.js';
import type { PenpotCapabilities, PenpotRemoteObject } from './mcp/types.js';
import type { VisualRenderTarget } from './visual/renderModel.js';

export type LivePlanItem = {
  repoId:string;
  action:'create'|'update'|'unchanged'|'orphan'|'unsupported';
  operation?:PenpotOperation;
  current?:PenpotRemoteObject;
  visualTarget?:VisualRenderTarget;
  structuralDrift?:boolean;
  visualDrift?:boolean;
};

function normalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value as Record<string, unknown>).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,normalize(v)]));
  return value;
}

export function buildLivePlan(desired: PenpotOperation[], current: PenpotRemoteObject[], capabilities: PenpotCapabilities, visualTargets: VisualRenderTarget[] = []): LivePlanItem[] {
  const byId = new Map(current.filter(x=>x.repoId).map(x=>[x.repoId!, x]));
  const desiredIds = new Set(desired.map(x=>x.repoId));
  const visualById = new Map(visualTargets.map(x=>[x.repoId,x]));
  const out: LivePlanItem[] = [];
  for (const op of desired) {
    const cur = byId.get(op.repoId);
    const visualTarget = visualById.get(op.repoId);
    if (op.kind === 'ensure-prototype-link' && !capabilities.prototype.supported) { out.push({repoId:op.repoId,action:'unsupported',operation:op,current:cur}); continue; }
    if (!cur) { out.push({repoId:op.repoId,action:'create',operation:op,visualTarget,structuralDrift:true,visualDrift:Boolean(visualTarget)}); continue; }
    const sameKind = cur.kind === op.kind;
    const sameName = op.kind !== 'ensure-page' || cur.name === op.name;
    const samePayload = op.kind === 'ensure-page' || JSON.stringify(normalize(cur.payload)) === JSON.stringify(normalize(op.payload));
    const structuralDrift = !(sameKind && sameName && samePayload);
    const visualDrift = Boolean(visualTarget && (cur.visual?.version !== visualTarget.renderVersion || cur.visual?.fingerprint !== visualTarget.fingerprint));
    out.push({repoId:op.repoId,action:structuralDrift||visualDrift?'update':'unchanged',operation:op,current:cur,visualTarget,structuralDrift,visualDrift});
  }
  for (const cur of current.filter(x=>x.repoId && !desiredIds.has(x.repoId)).sort((a,b)=>a.repoId!.localeCompare(b.repoId!))) out.push({repoId:cur.repoId!,action:'orphan',current:cur});
  return out;
}
