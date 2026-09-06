import { describe, expect, it } from 'vitest';
import { loadProject } from '../src/loadProject.js';
import { buildPlan } from '../src/plan.js';
import { buildWorkspaceTargets } from '../src/workspace/layout.js';

describe('workspace layout',()=>{
  it('places managed roots into deterministic non-overlapping zones',async()=>{
    const desired=buildPlan(await loadProject(process.cwd()));
    const targets=buildWorkspaceTargets(desired);
    const byId=new Map(targets.map(x=>[x.repoId,x]));

    expect(byId.get('page:components')).toMatchObject({x:100,y:100});
    expect(byId.get('page:b2c')).toMatchObject({x:1600,y:100});
    expect(byId.get('screen:b2c-home')).toMatchObject({x:1600,y:300});
    expect(byId.get('screen:b2c-category')).toMatchObject({x:2050,y:300});
    expect(byId.get('screen:b2c-product')).toMatchObject({x:2500,y:300});
    expect(byId.get('page:b2b')).toMatchObject({x:5200,y:100});

    const screenTargets=targets.filter(x=>x.repoId.startsWith('screen:'));
    expect(new Set(screenTargets.map(x=>`${x.x},${x.y}`)).size).toBe(screenTargets.length);
    expect(targets.some(x=>x.repoId.startsWith('tokens:'))).toBe(false);
  });
});
