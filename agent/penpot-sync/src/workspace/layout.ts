import type { PenpotOperation } from '../adapter.js';

export type WorkspaceTarget = { repoId:string; version:'v1'; x:number; y:number };

const PAGE_POSITIONS: Record<string,{x:number;y:number}> = {
  'page:foundations': {x:-1500,y:100},
  'page:components': {x:100,y:100},
  'page:b2c': {x:1600,y:100},
  'page:b2b': {x:5200,y:100},
  'page:prototype': {x:8800,y:100}
};

const B2C_ORDER = ['b2c-home','b2c-category','b2c-product','b2c-search','b2c-cart','b2c-checkout','b2c-confirmation','b2c-tracking','b2c-orders','b2c-login','b2c-signup'];
const B2B_ORDER = ['b2b-home','b2b-category','b2b-product','b2b-search','b2b-cart','b2b-checkout','b2b-confirmation','b2b-orders'];

function grid(repoIds:string[], x0:number, y0:number, columns:number, dx:number, dy:number): WorkspaceTarget[] {
  return repoIds.map((repoId,index)=>({repoId,version:'v1',x:x0+(index%columns)*dx,y:y0+Math.floor(index/columns)*dy}));
}

function orderScreens(ids:string[], preferred:string[]): string[] {
  const rank=new Map(preferred.map((id,index)=>[`screen:${id}`,index]));
  return [...ids].sort((a,b)=>(rank.get(a)??999)-(rank.get(b)??999)||a.localeCompare(b));
}

export function buildWorkspaceTargets(operations: PenpotOperation[]): WorkspaceTarget[] {
  const targets:WorkspaceTarget[]=[];
  for(const op of operations) {
    if(op.kind==='ensure-page') {
      const pos=PAGE_POSITIONS[op.repoId];
      if(pos) targets.push({repoId:op.repoId,version:'v1',...pos});
    }
  }

  const components=operations.filter(x=>x.kind==='ensure-component').map(x=>x.repoId);
  targets.push(...grid(components,100,300,4,380,180));

  const b2c=orderScreens(operations.filter(x=>x.kind==='ensure-screen'&&x.repoId.startsWith('screen:b2c-')).map(x=>x.repoId),B2C_ORDER);
  targets.push(...grid(b2c,1600,300,3,450,980));

  const b2b=orderScreens(operations.filter(x=>x.kind==='ensure-screen'&&x.repoId.startsWith('screen:b2b-')).map(x=>x.repoId),B2B_ORDER);
  targets.push(...grid(b2b,5200,300,3,450,980));

  return targets;
}
