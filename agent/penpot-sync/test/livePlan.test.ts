import { describe, expect, it } from 'vitest';
import { buildLivePlan } from '../src/livePlan.js';
import type { PenpotCapabilities } from '../src/mcp/types.js';

const caps: PenpotCapabilities = {read:{supported:true,tool:'execute_code'},create:{supported:true,tool:'execute_code'},update:{supported:true,tool:'execute_code'},prototype:{supported:false}};

describe('buildLivePlan',()=>{
  it('classifies create update unchanged orphan and unsupported without delete',()=>{
    const desired:any[]=[
      {kind:'ensure-page',repoId:'page:a',name:'A'},
      {kind:'ensure-token-set',repoId:'tokens:a',payload:{colors:{primary:'#000000'}}},
      {kind:'ensure-prototype-link',repoId:'route:a',payload:{}}
    ];
    const current:any[]=[
      {repoId:'page:a',remoteId:'1',kind:'ensure-page',name:'A',payload:{name:'A'}},
      {repoId:'tokens:a',remoteId:'2',kind:'ensure-token-set',payload:{colors:{primary:'#FFFFFF'}}},
      {repoId:'orphan:x',remoteId:'3',kind:'ensure-screen',payload:{}}
    ];
    const plan=buildLivePlan(desired,current,caps);
    expect(plan.find(x=>x.repoId==='page:a')?.action).toBe('unchanged');
    expect(plan.find(x=>x.repoId==='tokens:a')?.action).toBe('update');
    expect(plan.find(x=>x.repoId==='route:a')?.action).toBe('unsupported');
    expect(plan.find(x=>x.repoId==='orphan:x')?.action).toBe('orphan');
    expect(plan.some(x=>(x.action as string)==='delete')).toBe(false);
  });
});
