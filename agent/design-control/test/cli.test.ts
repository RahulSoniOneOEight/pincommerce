import { mkdtemp, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { describe, expect, it, vi } from 'vitest';
import { run } from '../src/cli.js';

describe('design control CLI',()=>{
  it('validates the repository design contract',async()=>{
    let output='';
    const log=vi.spyOn(console,'log').mockImplementation(v=>{output+=String(v);});
    expect(await run(['validate'],process.cwd())).toBe(0);
    log.mockRestore();
    expect(JSON.parse(output)).toEqual({valid:true,briefs:['b2c-home']});
  });

  it('prints the requested handoff brief',async()=>{
    let output='';
    const log=vi.spyOn(console,'log').mockImplementation(v=>{output+=String(v);});
    expect(await run(['brief','--screen','b2c-home'],process.cwd())).toBe(0);
    log.mockRestore();
    expect(output).toContain('Penpot AI Kit Handoff');
    expect(output).toContain('Flash Deals');
  });

  it('writes a deterministic run manifest',async()=>{
    const dir=await mkdtemp(path.join(os.tmpdir(),'pincommerce-design-'));
    const out=path.join(dir,'design-run.json');
    expect(await run(['run-manifest','--screen','b2c-home','--out',out],process.cwd())).toBe(0);
    const first=await readFile(out,'utf8');
    expect(await run(['run-manifest','--screen','b2c-home','--out',out],process.cwd())).toBe(0);
    const second=await readFile(out,'utf8');
    expect(first).toBe(second);
    expect(first).not.toMatch(/userToken=|PENPOT_MCP_URL|OPENAI_API_KEY/);
  });

  it('returns non-zero for an unknown screen',async()=>{
    const error=vi.spyOn(console,'error').mockImplementation(()=>{});
    expect(await run(['brief','--screen','missing'],process.cwd())).toBe(1);
    error.mockRestore();
  });
});
