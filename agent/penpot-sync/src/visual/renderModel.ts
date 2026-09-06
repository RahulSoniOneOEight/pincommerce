import { createHash } from 'node:crypto';
import type { RenderNode, VisualProjectInput } from './schema.js';
import { VISUAL_RENDER_BUILD, VISUAL_RENDER_VERSION } from './registry.js';

export type VisualRenderTarget = {
  repoId:string;
  targetKind:'component'|'screen';
  renderVersion:'v1';
  tree:RenderNode;
  fingerprint:string;
};

function normalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value as Record<string,unknown>).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,normalize(v)]));
  return value;
}

export function stableVisualFingerprint(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(normalize(value))).digest('hex');
}

function prefixIds(node: RenderNode, prefix:string): RenderNode {
  if (node.type === 'frame') return {...node,id:`${prefix}.${node.id}`,children:node.children.map(c=>prefixIds(c,prefix))};
  return {...node,id:`${prefix}.${node.id}`};
}

function materialize(node: RenderNode, componentMap: Map<string,RenderNode>): RenderNode {
  if (node.type === 'component-instance') {
    const source = componentMap.get(node.componentId);
    if (!source) return {id:node.id,type:'frame',x:node.x,y:node.y,width:120,height:44,children:[]};
    const cloned = prefixIds(source,node.id);
    const positioned = cloned.type === 'frame' ? {...cloned,x:node.x,y:node.y} : cloned;
    return materialize(positioned,componentMap);
  }
  if (node.type === 'frame') return {...node,children:node.children.map(c=>materialize(c,componentMap))};
  return node;
}

function fingerprint(themeId:string, tree:RenderNode): string {
  return stableVisualFingerprint({theme:themeId,version:VISUAL_RENDER_VERSION,build:VISUAL_RENDER_BUILD,tree});
}

export function buildVisualRenderTargets(input: VisualProjectInput): VisualRenderTarget[] {
  const componentMap = new Map(input.components.map(c=>[c.id,c.root]));
  const components = input.components.map(component => {
    const tree = materialize(component.root, componentMap);
    const base = {repoId:`component:${component.id}`,targetKind:'component' as const,renderVersion:VISUAL_RENDER_VERSION,tree};
    return {...base,fingerprint:fingerprint(input.theme.id,tree)};
  });
  const screens = input.screens.map(screen => {
    const tree: RenderNode = {id:'screen-root',type:'frame',width:input.theme.canvas.width,height:input.theme.canvas.height,fill:input.theme.colors.background,children:screen.sections.map(s=>materialize(s.root,componentMap))};
    const base = {repoId:`screen:${screen.id}`,targetKind:'screen' as const,renderVersion:VISUAL_RENDER_VERSION,tree};
    return {...base,fingerprint:fingerprint(input.theme.id,tree)};
  });
  return [...components,...screens];
}
