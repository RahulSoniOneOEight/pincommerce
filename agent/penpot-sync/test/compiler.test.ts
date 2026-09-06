import { describe, expect, it } from 'vitest';
import { compileVisualRenderCode } from '../src/visual/compiler.js';

describe('compileVisualRenderCode',()=>{
  const target:any={repoId:'component:button',targetKind:'component',renderVersion:'v1',fingerprint:'abc',tree:{id:'root',type:'frame',width:120,height:44,children:[{id:'label',type:'text',x:10,y:10,text:'Go',role:'label'}]}};
  it('targets existing managed root and names only renderer-owned children',()=>{
    const code=compileVisualRenderCode(target,'root-123');
    expect(code).toContain("getShapeById(remoteRootId)");
    expect(code).toContain('PCV1::component:button::');
    expect(code).not.toContain('root.remove()');
  });
  it('contains no network primitive',()=>{
    const code=compileVisualRenderCode(target,'root-123');
    expect(code).not.toMatch(/fetch\(|XMLHttpRequest|https?:\/\//);
  });
});
