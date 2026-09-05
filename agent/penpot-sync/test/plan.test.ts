import { describe, expect, it } from 'vitest';
import { loadProject } from '../src/loadProject.js';
import { buildPlan } from '../src/plan.js';

describe('buildPlan', () => {
  it('is deterministic and ordered', async () => {
    const project = await loadProject(process.cwd());
    const a = buildPlan(project);
    const b = buildPlan(project);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
    expect(a[0]).toMatchObject({kind:'ensure-page', repoId:'page:foundations'});
    const kinds = a.map(x => x.kind);
    expect(kinds.indexOf('ensure-component')).toBeGreaterThan(kinds.indexOf('ensure-token-set'));
    expect(kinds.lastIndexOf('ensure-prototype-link')).toBe(a.length - 1);
  });

  it('uses stable unique repository ids', async () => {
    const project = await loadProject(process.cwd());
    const ids = buildPlan(project).map(x => x.repoId);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
