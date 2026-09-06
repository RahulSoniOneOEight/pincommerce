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
  it('uses a container shape for icons before appending glyph children',()=>{
    const iconTarget:any={repoId:'component:test-icon',targetKind:'component',renderVersion:'v1',fingerprint:'icon-fp',tree:{id:'root',type:'frame',width:64,height:64,children:[{id:'icon',type:'icon',x:8,y:8,width:32,height:32,recipe:'utility',color:'#173B72'}]}};
    const code=compileVisualRenderCode(iconTarget,'root-123');
    const start=code.indexOf("else if(node.type==='icon')");
    expect(start).toBeGreaterThanOrEqual(0);
    const end=code.indexOf('if(!s)return null',start);
    expect(end).toBeGreaterThan(start);
    const iconBranch=code.slice(start,end);
    expect(iconBranch).toContain('penpot.createBoard()');
    expect(iconBranch).not.toContain('penpot.createRectangle()');
    expect(iconBranch).toContain('s.appendChild(g)');
  });
});
