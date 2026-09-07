import { describe, expect, it } from 'vitest';
import { buildLivePlan } from '../src/livePlan.js';

const caps:any={read:{supported:true},create:{supported:true},update:{supported:true},prototype:{supported:false}};
const desired:any[]=[{kind:'ensure-screen',repoId:'screen:b2c-home',payload:{components:['header']}}];
const target:any={repoId:'screen:b2c-home',targetKind:'screen',renderVersion:'v1',tree:{id:'root',type:'frame',width:390,height:844,children:[]},fingerprint:'new'};

describe('visual-aware live plan',()=>{
  it('marks structural match as update when visual fingerprint differs',()=>{
    const current:any[]=[{repoId:'screen:b2c-home',remoteId:'1',kind:'ensure-screen',payload:{components:['header']},visual:{version:'v1',fingerprint:'old'}}];
    const item=buildLivePlan(desired,current,caps,[target])[0];
    expect(item.action).toBe('update');
    expect(item.structuralDrift).toBe(false);
    expect(item.visualDrift).toBe(true);
  });
  it('is unchanged when both structural and visual state match',()=>{
    const current:any[]=[{repoId:'screen:b2c-home',remoteId:'1',kind:'ensure-screen',payload:{components:['header']},visual:{version:'v1',fingerprint:'new'}}];
    expect(buildLivePlan(desired,current,caps,[target])[0].action).toBe('unchanged');
  });
});
