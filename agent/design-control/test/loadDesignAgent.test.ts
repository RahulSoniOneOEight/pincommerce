import { describe, expect, it } from 'vitest';
import { loadDesignAgent } from '../src/loadDesignAgent.js';

describe('design agent project',()=>{
  it('loads the production b2c-home brief',async()=>{
    const project=await loadDesignAgent(process.cwd());
    expect(project.config.defaultWorkflow).toBe('brief-to-screen');
    expect(project.briefs.get('b2c-home')?.viewport).toBe('390x844');
    expect(project.briefs.get('b2c-home')?.theme).toBe('theme-b-blue');
  });

  it('contains no secret-bearing values',async()=>{
    const project=await loadDesignAgent(process.cwd());
    expect(JSON.stringify(project)).not.toMatch(/userToken=|PENPOT_MCP_URL|OPENAI_API_KEY|sk-[A-Za-z0-9_-]+/);
  });
});
