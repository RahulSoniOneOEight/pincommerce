import { describe, expect, it } from 'vitest';
import { loadProject } from '../src/loadProject.js';

describe('loadProject', () => {
  it('loads and validates repository manifests', async () => {
    const project = await loadProject(process.cwd());
    expect(project.themes.map(t => t.id)).toEqual(['theme-a-green', 'theme-b-blue']);
    expect(project.components.length).toBeGreaterThan(10);
    expect(project.b2cScreens.some(s => s.id === 'b2c-checkout')).toBe(true);
    expect(project.b2bScreens.some(s => s.id === 'b2b-checkout')).toBe(true);
  });

  it('reports missing manifest paths', async () => {
    await expect(loadProject('/definitely/missing')).rejects.toThrow('design-system/tokens/foundations.json');
  });
});
