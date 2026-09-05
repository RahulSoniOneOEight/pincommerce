import type { ProjectDefinition } from './schema.js';
import type { PenpotOperation } from './adapter.js';

export function buildPlan(project: ProjectDefinition): PenpotOperation[] {
  const ops: PenpotOperation[] = [];
  ops.push({ kind: 'ensure-page', repoId: 'page:foundations', name: '01 Foundations' });
  ops.push({ kind: 'ensure-token-set', repoId: 'tokens:foundations', payload: project.foundations });
  ops.push({ kind: 'ensure-token-set', repoId: `tokens:${project.themes[0].id}`, payload: project.themes[0] });
  ops.push({ kind: 'ensure-token-set', repoId: `tokens:${project.themes[1].id}`, payload: project.themes[1] });
  ops.push({ kind: 'ensure-page', repoId: 'page:components', name: '02 Components' });
  for (const component of [...project.components].sort((a,b)=>a.id.localeCompare(b.id))) ops.push({ kind: 'ensure-component', repoId: `component:${component.id}`, payload: component });
  ops.push({ kind: 'ensure-page', repoId: 'page:b2c', name: '03 B2C Screens' });
  for (const screen of [...project.b2cScreens].sort((a,b)=>a.id.localeCompare(b.id))) ops.push({ kind: 'ensure-screen', repoId: `screen:${screen.id}`, payload: screen });
  ops.push({ kind: 'ensure-page', repoId: 'page:b2b', name: '04 B2B Screens' });
  for (const screen of [...project.b2bScreens].sort((a,b)=>a.id.localeCompare(b.id))) ops.push({ kind: 'ensure-screen', repoId: `screen:${screen.id}`, payload: screen });
  ops.push({ kind: 'ensure-page', repoId: 'page:prototype', name: '05 Prototype' });
  for (const route of [...project.routes].sort((a,b)=>a.id.localeCompare(b.id))) ops.push({ kind: 'ensure-prototype-link', repoId: `route:${route.id}`, payload: route });
  return ops;
}
