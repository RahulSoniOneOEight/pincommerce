import 'dotenv/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadPenpotConfig } from './config.js';
import { loadProject } from './loadProject.js';
import { buildPlan } from './plan.js';
import { buildLivePlan } from './livePlan.js';
import { RemoteMcpTransport } from './mcp/transport.js';
import { PenpotMcpGateway } from './mcp/gateway.js';
import { McpPenpotAdapter } from './adapters/mcp.js';
import type { McpTransport } from './mcp/types.js';
import { loadVisualProject } from './visual/loadVisualProject.js';
import { buildVisualRenderTargets } from './visual/renderModel.js';

export type LiveCliDeps = { transport?: McpTransport; env?: NodeJS.ProcessEnv; log?: (value:string)=>void; error?: (value:string)=>void };

function counts(items: ReturnType<typeof buildLivePlan>) {
  return items.reduce((a,x)=>{a[x.action]++; return a;},{create:0,update:0,unchanged:0,orphan:0,unsupported:0} as Record<'create'|'update'|'unchanged'|'orphan'|'unsupported',number>);
}

export async function runLive(argv = process.argv.slice(2), root = process.cwd(), deps: LiveCliDeps = {}): Promise<number> {
  const command = argv[0];
  const log = deps.log ?? console.log;
  const error = deps.error ?? console.error;
  if (command === 'sync' && !argv.includes('--apply')) { error('CONFIG_ERROR: live sync requires --apply'); return 2; }
  let transport: McpTransport | undefined;
  try {
    const config = loadPenpotConfig(deps.env ?? process.env);
    transport = deps.transport ?? new RemoteMcpTransport(config);
    await transport.connect();
    const gateway = new PenpotMcpGateway(transport, config);
    const capabilities = await gateway.discover();
    const target = await gateway.inspectTarget();
    if (command === 'check') {
      log(JSON.stringify({ connected:true, target, capabilities:{read:capabilities.read.supported,create:capabilities.create.supported,update:capabilities.update.supported,prototype:capabilities.prototype.supported} }));
      return 0;
    }
    const project = await loadProject(root);
    const desired = buildPlan(project);
    const visualProject = await loadVisualProject(root);
    const visualTargets = buildVisualRenderTargets(visualProject);
    if (command === 'plan') {
      const current = await gateway.listManagedObjects();
      log(JSON.stringify(counts(buildLivePlan(desired,current,capabilities,visualTargets))));
      return 0;
    }
    if (command === 'sync') {
      const result = await new McpPenpotAdapter(gateway).apply(desired,visualTargets);
      log(JSON.stringify(result));
      return result.failed === 0 ? 0 : 1;
    }
    if (command === 'verify') {
      const current = await gateway.listManagedObjects();
      const live = buildLivePlan(desired,current,capabilities,visualTargets);
      const drift = live.filter(x=>x.action==='create'||x.action==='update');
      if (drift.length) { error(`VERIFY_ERROR: ${drift.length} managed object(s) differ`); return 1; }
      log(JSON.stringify({ verified:true, ...counts(live) }));
      return 0;
    }
    error('Usage: liveCli.ts check | plan | sync --apply | verify');
    return 2;
  } catch (e) {
    error(e instanceof Error ? e.message : String(e));
    return 1;
  } finally {
    if (transport) { try { await transport.close(); } catch {} }
  }
}

const self = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(self)) process.exit(await runLive());
