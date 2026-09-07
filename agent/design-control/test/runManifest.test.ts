import { describe, expect, it } from 'vitest';
import { loadDesignAgent } from '../src/loadDesignAgent.js';
import { buildRunManifest, stableManifestJson } from '../src/runManifest.js';

describe('design run manifest',()=>{
  it('is deterministic and secret free',async()=>{
    const project=await loadDesignAgent(process.cwd());
    const first=buildRunManifest(project,'b2c-home');
    const second=buildRunManifest(project,'b2c-home');
    expect(first).toEqual(second);
    expect(first.screenId).toBe('b2c-home');
    expect(first.workflow).toBe('brief-to-screen');
    expect(first.viewport).toBe('390x844');
    expect(first.briefSha256).toMatch(/^[a-f0-9]{64}$/);
    expect(stableManifestJson(first)).toBe(stableManifestJson(second));
    expect(stableManifestJson(first)).not.toMatch(/userToken=|PENPOT_MCP_URL|OPENAI_API_KEY|sk-[A-Za-z0-9_-]+/);
  });
});
