import { describe, expect, it } from 'vitest';
import { loadDesignAgent } from '../src/loadDesignAgent.js';
import { buildHandoff } from '../src/handoff.js';

describe('Penpot AI Kit handoff',()=>{
  it('builds a self-contained b2c-home handoff without secrets',async()=>{
    const project=await loadDesignAgent(process.cwd());
    const text=buildHandoff(project,'b2c-home');
    expect(text).toContain('brief-to-screen');
    expect(text).toContain('390x844');
    expect(text).toContain('Theme B');
    expect(text).toContain('Flash Deals');
    expect(text).toContain('npm run penpot:check');
    expect(text).toContain('direction-approval');
    expect(text).not.toMatch(/userToken=|PENPOT_MCP_URL|OPENAI_API_KEY|sk-[A-Za-z0-9_-]+/);
  });

  it('rejects an unknown screen',async()=>{
    const project=await loadDesignAgent(process.cwd());
    expect(()=>buildHandoff(project,'missing-screen')).toThrow(/unknown screen/i);
  });
});
