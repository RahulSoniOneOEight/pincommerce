import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

async function json(rel: string) { return JSON.parse(await readFile(path.join(process.cwd(), rel), 'utf8')); }

describe('theme token contract', () => {
  it('shares semantic keys and constrains premium watermark opacity', async () => {
    const a = await json('design-system/tokens/theme-a-green.json');
    const b = await json('design-system/tokens/theme-b-blue.json');
    const keys = ['primary','primaryForeground','background','surface','surfaceMuted','text','textMuted','border','accent','accentForeground'];
    for (const key of keys) { expect(a.colors[key]).toBeTruthy(); expect(b.colors[key]).toBeTruthy(); }
    expect(a.decoration.watermarkOpacity).toBe(0);
    expect(b.decoration.watermarkOpacity).toBeGreaterThanOrEqual(0.02);
    expect(b.decoration.watermarkOpacity).toBeLessThanOrEqual(0.04);
  });
});
