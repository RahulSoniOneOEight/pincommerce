import { describe, expect, it } from 'vitest';
import { loadVisualProject } from '../src/visual/loadVisualProject.js';
import { buildVisualRenderTargets, stableVisualFingerprint } from '../src/visual/renderModel.js';

describe('visual render model',()=>{
  it('builds stable component and three screen targets',async()=>{
    const project=await loadVisualProject(process.cwd());
    const first=buildVisualRenderTargets(project);
    const second=buildVisualRenderTargets(JSON.parse(JSON.stringify(project)));
    expect(first.map(x=>x.repoId)).toEqual(second.map(x=>x.repoId));
    expect(first.map(x=>x.fingerprint)).toEqual(second.map(x=>x.fingerprint));
    expect(first.filter(x=>x.targetKind==='screen').map(x=>x.repoId)).toEqual(['screen:b2c-home','screen:b2c-category','screen:b2c-product']);
  });
  it('sorts object keys without reordering arrays',()=>{
    expect(stableVisualFingerprint({b:2,a:[2,1]})).toBe(stableVisualFingerprint({a:[2,1],b:2}));
    expect(stableVisualFingerprint({a:[2,1]})).not.toBe(stableVisualFingerprint({a:[1,2]}));
  });
  it('keeps component child coordinates local when placing an instance on a screen',async()=>{
    const project=await loadVisualProject(process.cwd());
    const home=buildVisualRenderTargets(project).find(x=>x.repoId==='screen:b2c-home')!;
    expect(home.tree.type).toBe('frame');
    if(home.tree.type!=='frame') throw new Error('expected frame');
    const header=home.tree.children.find(x=>x.id==='header-inst.root');
    expect(header?.type).toBe('frame');
    if(!header || header.type!=='frame') throw new Error('expected header frame');
    expect(header.x).toBe(16);
    expect(header.y).toBe(16);
    const brand=header.children.find(x=>x.id==='header-inst.brand');
    expect(brand?.type).toBe('text');
    if(!brand || brand.type!=='text') throw new Error('expected brand text');
    expect(brand.x).toBe(16);
    expect(brand.y).toBe(14);
  });
});
