import { describe, expect, it } from 'vitest';
import { McpPenpotAdapter } from '../src/adapters/mcp.js';

const caps:any={read:{supported:true},create:{supported:true},update:{supported:true},prototype:{supported:false}};

describe('McpPenpotAdapter',()=>{
  it('writes creates and leaves unsupported routes untouched',async()=>{
    const created:string[]=[];
    const gateway:any={discover:async()=>caps,inspectTarget:async()=>({fileId:'f',pageId:'p'}),listManagedObjects:async()=>[],create:async(op:any)=>{created.push(op.repoId);return{remoteId:'x'}},update:async()=>{},renderVisual:async()=>{}};
    const result=await new McpPenpotAdapter(gateway).apply([{kind:'ensure-page',repoId:'page:a',name:'A'},{kind:'ensure-prototype-link',repoId:'route:a',payload:{}}] as any);
    expect(created).toEqual(['page:a']);
    expect(result.created).toBe(1);
    expect(result.unchanged).toBe(1);
  });
  it('surfaces partial write errors by repoId',async()=>{
    const gateway:any={discover:async()=>caps,inspectTarget:async()=>({fileId:'f',pageId:'p'}),listManagedObjects:async()=>[],create:async(op:any)=>{if(op.repoId==='bad')throw new Error('boom');return{remoteId:'x'}},update:async()=>{},renderVisual:async()=>{}};
    const result=await new McpPenpotAdapter(gateway).apply([{kind:'ensure-page',repoId:'ok',name:'A'},{kind:'ensure-page',repoId:'bad',name:'B'}] as any);
    expect(result.created).toBe(1); expect(result.failed).toBe(1); expect(result.errors[0].repoId).toBe('bad');
  });
  it('renders visual drift into an existing root without creating a duplicate',async()=>{
    const calls:string[]=[];
    const current:any={repoId:'screen:b2c-home',remoteId:'screen-root',kind:'ensure-screen',payload:{components:['header']}};
    const gateway:any={discover:async()=>caps,inspectTarget:async()=>({fileId:'f',pageId:'p'}),listManagedObjects:async()=>[current],create:async()=>{calls.push('create');return{remoteId:'new'}},update:async()=>calls.push('update'),renderVisual:async()=>calls.push('render')};
    const operations:any[]=[{kind:'ensure-screen',repoId:'screen:b2c-home',payload:{components:['header']}}];
    const visuals:any[]=[{repoId:'screen:b2c-home',targetKind:'screen',renderVersion:'v1',tree:{id:'root',type:'frame',width:390,height:844,children:[]},fingerprint:'fp'}];
    const result=await new McpPenpotAdapter(gateway).apply(operations,visuals);
    expect(calls).toEqual(['render']);
    expect(result.updated).toBe(1);
    expect(result.created).toBe(0);
  });
  it('isolates a visual failure to its repoId and continues other renders',async()=>{
    const current:any[]=[
      {repoId:'screen:b2c-home',remoteId:'home',kind:'ensure-screen',payload:{}},
      {repoId:'screen:b2c-product',remoteId:'product',kind:'ensure-screen',payload:{}}
    ];
    const rendered:string[]=[];
    const gateway:any={discover:async()=>caps,inspectTarget:async()=>({fileId:'f',pageId:'p'}),listManagedObjects:async()=>current,create:async()=>({remoteId:'new'}),update:async()=>{},renderVisual:async(t:any)=>{if(t.repoId==='screen:b2c-home')throw new Error('visual boom'); rendered.push(t.repoId)}};
    const operations:any[]=[{kind:'ensure-screen',repoId:'screen:b2c-home',payload:{}},{kind:'ensure-screen',repoId:'screen:b2c-product',payload:{}}];
    const visuals:any[]=operations.map(x=>({repoId:x.repoId,targetKind:'screen',renderVersion:'v1',tree:{id:'root',type:'frame',width:390,height:844,children:[]},fingerprint:'fp'}));
    const result=await new McpPenpotAdapter(gateway).apply(operations,visuals);
    expect(result.failed).toBe(1);
    expect(result.errors[0].repoId).toBe('screen:b2c-home');
    expect(rendered).toEqual(['screen:b2c-product']);
  });
});
