import { describe, expect, it } from 'vitest';
import { McpPenpotAdapter } from '../src/adapters/mcp.js';

const caps:any={read:{supported:true},create:{supported:true},update:{supported:true},prototype:{supported:false}};

describe('McpPenpotAdapter',()=>{
  it('writes creates and leaves unsupported routes untouched',async()=>{
    const created:string[]=[];
    const gateway:any={discover:async()=>caps,inspectTarget:async()=>({fileId:'f',pageId:'p'}),listManagedObjects:async()=>[],create:async(op:any)=>{created.push(op.repoId);return{remoteId:'x'}},update:async()=>{}};
    const result=await new McpPenpotAdapter(gateway).apply([{kind:'ensure-page',repoId:'page:a',name:'A'},{kind:'ensure-prototype-link',repoId:'route:a',payload:{}}] as any);
    expect(created).toEqual(['page:a']);
    expect(result.created).toBe(1);
    expect(result.unchanged).toBe(1);
  });
  it('surfaces partial write errors by repoId',async()=>{
    const gateway:any={discover:async()=>caps,inspectTarget:async()=>({fileId:'f',pageId:'p'}),listManagedObjects:async()=>[],create:async(op:any)=>{if(op.repoId==='bad')throw new Error('boom');return{remoteId:'x'}},update:async()=>{}};
    const result=await new McpPenpotAdapter(gateway).apply([{kind:'ensure-page',repoId:'ok',name:'A'},{kind:'ensure-page',repoId:'bad',name:'B'}] as any);
    expect(result.created).toBe(1); expect(result.failed).toBe(1); expect(result.errors[0].repoId).toBe('bad');
  });
});
