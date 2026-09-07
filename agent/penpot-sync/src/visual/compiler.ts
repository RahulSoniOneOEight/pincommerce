import type { RenderNode } from './schema.js';
import type { VisualRenderTarget } from './renderModel.js';

function js(value: unknown): string { return JSON.stringify(value); }

export function compileVisualRenderCode(target: VisualRenderTarget, remoteRootId: string): string {
  const prefix = `PCV1::${target.repoId}::`;
  const tree = js(target.tree);
  const repoId = js(target.repoId);
  const remote = js(remoteRootId);
  const fingerprint = js(target.fingerprint);
  return `const repoId=${repoId}; const remoteRootId=${remote}; const prefix=${js(prefix)}; const tree=${tree};\n` +
    `let root=penpot.currentPage?.getShapeById(remoteRootId)||null; if(!root){root=penpot.currentPage?.findShapes({name:'PC::'+repoId})?.[0]||null;} if(!root) throw new Error('VISUAL_TARGET_ERROR: managed root not found '+repoId);\n` +
    `for(const child of [...(root.children||[])]){if((child.name||'').startsWith(prefix)) child.remove();}\n` +
    `if(tree.width&&tree.height&&root.resize) root.resize(tree.width,tree.height);\n` +
    `const roleSize={display:22,title:18,body:13,label:12,caption:10,price:20};\n` +
    `const roleWeight={display:700,title:700,body:400,label:600,caption:500,price:700};\n` +
    `const render=(node,parent,ox,oy)=>{let s=null; const x=ox+(node.x||0), y=oy+(node.y||0);\n` +
    `if(node.type==='frame'){s=penpot.createBoard(); s.resize(node.width,node.height); if(node.fill)s.fills=[{fillColor:node.fill,fillOpacity:node.opacity??1}]; if(node.radius!=null)s.borderRadius=node.radius;}\n` +
    `else if(node.type==='rect'){s=penpot.createRectangle(); s.resize(node.width,node.height); s.fills=[{fillColor:node.fill,fillOpacity:node.opacity??1}]; if(node.radius!=null)s.borderRadius=node.radius;}\n` +
    `else if(node.type==='text'){s=penpot.createText(node.text||' '); if(!s)return null; s.fontSize=String(node.size||roleSize[node.role]||12); s.fontWeight=String(node.weight||roleWeight[node.role]||400); s.fills=[{fillColor:node.color||'#111827',fillOpacity:node.opacity??1}]; if(node.width)s.resize(node.width,s.height);}\n` +
    `else if(node.type==='icon'){s=penpot.createBoard(); s.resize(node.width,node.height); s.fills=[{fillColor:node.color||'#173B72',fillOpacity:node.opacity??0.14}]; s.borderRadius=Math.min(node.width,node.height)/4; s.clipContent=false; const g=penpot.createText(({plumbing:'↔',electrical:'⚡',sanitary:'◫','paints-construction':'▧','hardware-tools':'⌁',agriculture:'⌁',search:'⌕',utility:'•••',delivery:'→','product-placeholder':'◆'}[node.recipe])||'◇'); if(g){g.fontSize=String(Math.max(12,Math.round(node.height*0.42))); g.fills=[{fillColor:node.color||'#173B72',fillOpacity:Math.min(1,(node.opacity??1)+0.35)}]; g.x=x+Math.max(4,node.width*0.28); g.y=y+Math.max(3,node.height*0.20); s.appendChild(g);}}\n` +
    `if(!s)return null; s.name=prefix+node.id; s.x=x; s.y=y; parent.appendChild(s); if(node.type==='frame'){for(const c of node.children||[])render(c,s,x,y);} return s;};\n` +
    `const start=(tree.type==='frame'?(tree.children||[]):[tree]); for(const n of start) render(n,root,root.x,root.y); return {repoId,fingerprint:${fingerprint},rendered:true};`;
}
