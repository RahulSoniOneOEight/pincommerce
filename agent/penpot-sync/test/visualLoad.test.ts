import { describe, expect, it } from 'vitest';
import { loadVisualProject } from '../src/visual/loadVisualProject.js';

describe('loadVisualProject',()=>{
  it('loads Theme B and only the first three B2C screens',async()=>{
    const visual=await loadVisualProject(process.cwd());
    expect(visual.theme.id).toBe('theme-b');
    expect(visual.screens.map(x=>x.id)).toEqual(['b2c-home','b2c-category','b2c-product']);
    expect(visual.components.some(x=>x.id==='product-card')).toBe(true);
  });
});
