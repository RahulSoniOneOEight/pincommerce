import { describe, expect, it, vi } from 'vitest';
import { run } from '../src/cli.js';

describe('cli', () => {
  it('validates a valid repo', async () => {
    const log = vi.spyOn(console, 'log').mockImplementation(() => {});
    expect(await run(['validate'], process.cwd())).toBe(0);
    log.mockRestore();
  });

  it('dry run emits a safe operation plan', async () => {
    let out = '';
    const log = vi.spyOn(console, 'log').mockImplementation(v => { out += String(v); });
    expect(await run(['sync:dry'], process.cwd())).toBe(0);
    log.mockRestore();
    const parsed = JSON.parse(out);
    expect(parsed.operationCount).toBeGreaterThan(0);
    expect(parsed.kinds).toContain('ensure-token-set');
    if (process.env.OPENAI_API_KEY) expect(out).not.toContain(process.env.OPENAI_API_KEY);
  });

  it('returns non-zero for an invalid root', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(await run(['validate'], '/definitely/missing')).toBe(1);
    error.mockRestore();
  });
});
