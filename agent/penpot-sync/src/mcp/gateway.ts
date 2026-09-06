import type { PenpotOperation } from '../adapter.js';
import type { PenpotConfig } from '../config.js';
import { redactText } from '../redact.js';
import { compileVisualRenderCode } from '../visual/compiler.js';
import type { VisualRenderTarget } from '../visual/renderModel.js';
import type { McpTransport, PenpotCapabilities, PenpotRemoteObject, PenpotTarget } from './types.js';

const REGISTRY_KEY = 'pincommerce.managed.v1';

function textResult(value: any): any {
  const content = value?.content;
  if (!Array.isArray(content)) return value;
  const text = content.find((x: any) => x?.type === 'text')?.text;
  if (typeof text !== 'string') return value;
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === 'object' && 'result' in parsed) return (parsed as any).result;
    return parsed;
  } catch { return text; }
}

function js(value: unknown): string { return JSON.stringify(value); }

export class PenpotMcpGateway {
  private capabilities?: PenpotCapabilities;
  constructor(private readonly transport: McpTransport, private readonly config: PenpotConfig) {}

  async discover(): Promise<PenpotCapabilities> {
    const tools = await this.transport.listTools();
    const byName = new Map(tools.map(t => [t.name, t]));
    const execute = byName.get('execute_code');
    if (!execute) throw new Error('MCP_CAPABILITY_ERROR: Penpot execute_code tool is required');
    this.capabilities = {
      read: { supported: true, tool: 'execute_code' },
      create: { supported: true, tool: 'execute_code' },
      update: { supported: true, tool: 'execute_code' },
      prototype: { supported: false }
    };
    return this.capabilities;
  }

  getCapabilities(): PenpotCapabilities {
    if (!this.capabilities) throw new Error('MCP_CAPABILITY_ERROR: discover() must run first');
    return this.capabilities;
  }

  private async execute(code: string): Promise<any> {
    return textResult(await this.transport.callTool('execute_code', { code }));
  }

  async inspectTarget(): Promise<PenpotTarget> {
    const target = await this.execute(`return {fileId: penpot.currentFile?.id, fileName: penpot.currentFile?.name, pageId: penpot.currentPage?.id, pageName: penpot.currentPage?.name};`);
    if (!target?.fileId || !target?.pageId) throw new Error('TARGET_ERROR: no active Penpot file/page is connected');
    if (this.config.expectedFileId && target.fileId !== this.config.expectedFileId) throw new Error(`TARGET_ERROR: connected file does not match PENPOT_FILE_ID`);
    return target;
  }

  async listManagedObjects(): Promise<PenpotRemoteObject[]> {
    const result = await this.execute(`const raw=penpot.library.local.getPluginData(${js(REGISTRY_KEY)}); if(!raw) return []; try { return JSON.parse(raw); } catch { return []; }`);
    return Array.isArray(result) ? result : [];
  }

  private createCode(op: PenpotOperation): string {
    const encoded = js(op);
    return `const op=${encoded}; const key=${js(REGISTRY_KEY)}; const raw=penpot.library.local.getPluginData(key); let reg=[]; try{reg=raw?JSON.parse(raw):[]}catch{}; let remoteId='';\n` +
      `if(op.kind==='ensure-page'){const b=penpot.createBoard(); b.name='PC::'+op.repoId+'::'+op.name; b.resize(1440,120); remoteId=b.id;}\n` +
      `else if(op.kind==='ensure-screen'){const b=penpot.createBoard(); b.name='PC::'+op.repoId; b.resize(390,844); const t=penpot.createText(op.repoId); if(t){t.x=b.x+24;t.y=b.y+24;b.appendChild(t);} remoteId=b.id;}\n` +
      `else if(op.kind==='ensure-component'){const b=penpot.createBoard(); b.name='PC::'+op.repoId; b.resize(320,120); const t=penpot.createText(op.repoId); if(t){t.x=b.x+16;t.y=b.y+16;b.appendChild(t);} const c=penpot.library.local.createComponent([b]); c.name=op.repoId.replace('component:',''); remoteId=c.id;}\n` +
      `else if(op.kind==='ensure-token-set'){const cat=penpot.library.local.tokens; const setName='PinCommerce/'+op.repoId; let s=cat.sets.find(x=>x.name===setName); if(!s)s=cat.addSet({name:setName}); const colors=op.payload?.colors||{}; for(const [n,v] of Object.entries(colors)){let tok=s.tokens.find(x=>x.name===n); if(!tok) tok=s.addToken({type:'color',name:n,value:String(v)}); else tok.value=String(v);} remoteId=s.id;}\n` +
      `else { throw new Error('unsupported operation '+op.kind); }\n` +
      `reg=reg.filter(x=>x.repoId!==op.repoId); reg.push({repoId:op.repoId,remoteId,kind:op.kind,name:op.name,payload:op.payload}); penpot.library.local.setPluginData(key,JSON.stringify(reg)); return {repoId:op.repoId,remoteId};`;
  }

  async create(op: PenpotOperation): Promise<{ remoteId: string }> {
    if (op.kind === 'ensure-prototype-link') throw new Error(`MCP_CAPABILITY_ERROR: prototype links are unsupported`);
    return this.execute(this.createCode(op));
  }

  async update(op: PenpotOperation, current: PenpotRemoteObject): Promise<void> {
    if (op.kind === 'ensure-prototype-link') throw new Error(`MCP_CAPABILITY_ERROR: prototype links are unsupported`);
    const encoded = js(op);
    await this.execute(`const op=${encoded}; const key=${js(REGISTRY_KEY)}; const raw=penpot.library.local.getPluginData(key); let reg=[]; try{reg=raw?JSON.parse(raw):[]}catch{}; const cur=reg.find(x=>x.repoId===op.repoId); if(!cur) throw new Error('managed object missing'); if(op.kind==='ensure-token-set'){const cat=penpot.library.local.tokens; const s=cat.sets.find(x=>x.id===cur.remoteId)||cat.sets.find(x=>x.name==='PinCommerce/'+op.repoId); if(s){const colors=op.payload?.colors||{}; for(const [n,v] of Object.entries(colors)){let tok=s.tokens.find(x=>x.name===n); if(!tok)tok=s.addToken({type:'color',name:n,value:String(v)}); else tok.value=String(v);}}} cur.kind=op.kind; cur.name=op.name; cur.payload=op.payload; penpot.library.local.setPluginData(key,JSON.stringify(reg)); return true;`);
  }

  async renderVisual(target: VisualRenderTarget, current: PenpotRemoteObject): Promise<void> {
    if (!current.remoteId) throw new Error(`VISUAL_TARGET_ERROR: managed root is missing for ${target.repoId}`);
    try {
      await this.execute(compileVisualRenderCode(target,current.remoteId));
      await this.execute(`const key=${js(REGISTRY_KEY)}; const raw=penpot.library.local.getPluginData(key); let reg=[]; try{reg=raw?JSON.parse(raw):[]}catch{}; const cur=reg.find(x=>x.repoId===${js(target.repoId)}); if(!cur) throw new Error('VISUAL_TARGET_ERROR: registry entry missing'); cur.visual={version:'v1',fingerprint:${js(target.fingerprint)}}; penpot.library.local.setPluginData(key,JSON.stringify(reg)); return true;`);
    } catch (error) {
      const message = redactText(error instanceof Error ? error.message : String(error));
      throw new Error(message.startsWith('VISUAL_') ? message : `VISUAL_RENDER_ERROR: ${message}`);
    }
  }

  async verify(op: PenpotOperation): Promise<boolean> {
    const items = await this.listManagedObjects();
    return items.some(x => x.repoId === op.repoId);
  }
}
