import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

describe('B2C home visual contract',()=>{
  it('captures the shared Make home merchandising structure',()=>{
    const file=path.join(process.cwd(),'screens/b2c/visual-v1.json');
    const json=JSON.parse(fs.readFileSync(file,'utf8'));
    const home=json.screens.find((screen:any)=>screen.id==='b2c-home');
    expect(home).toBeTruthy();
    const ids=new Set(home.sections.map((section:any)=>section.id));
    for(const id of ['header','search','hero','category-title','categories','brands-title','brands','flash-title','flash-products','rated-title','rated-products','nav']) {
      expect(ids.has(id),`missing ${id}`).toBe(true);
    }
    const hero=home.sections.find((section:any)=>section.id==='hero')?.root;
    expect(JSON.stringify(hero)).toContain('Big Construction Sale');
    expect(JSON.stringify(hero)).toContain('Shop Now');
    const categories=home.sections.find((section:any)=>section.id==='categories')?.root;
    expect((categories?.children||[]).filter((x:any)=>x.type==='icon').length).toBeGreaterThanOrEqual(6);
    expect(home.sections.find((section:any)=>section.id==='brands')?.root?.children?.length).toBeGreaterThanOrEqual(6);
    expect(home.sections.find((section:any)=>section.id==='flash-products')?.root?.children?.length).toBeGreaterThanOrEqual(2);
    expect(home.sections.find((section:any)=>section.id==='rated-products')?.root?.children?.length).toBeGreaterThanOrEqual(2);
  });
});
