import { describe, expect, it } from 'vitest';
import { PenpotMcpGateway } from '../src/mcp/gateway.js';
import { FakeMcpTransport, mcpText } from './fakes/fakeMcp.js';

describe('PenpotMcpGateway', () => {
  it('requires execute_code and exposes prototype as unsupported', async () => {
    const fake = new FakeMcpTransport([{name:'execute_code'},{name:'high_level_overview'}]);
    const gateway = new PenpotMcpGateway(fake,{mcpUrl:'https://example.test/mcp'});
    const caps = await gateway.discover();
    expect(fake.listCount).toBe(1);
    expect(caps.read.supported).toBe(true);
    expect(caps.prototype.supported).toBe(false);
  });
  it('rejects missing execute_code', async () => {
    const gateway = new PenpotMcpGateway(new FakeMcpTransport([]),{mcpUrl:'https://example.test/mcp'});
    await expect(gateway.discover()).rejects.toThrow('MCP_CAPABILITY_ERROR');
  });
  it('validates expected target file', async () => {
    const fake = new FakeMcpTransport(undefined,()=>mcpText({fileId:'wrong',pageId:'p1'}));
    const gateway = new PenpotMcpGateway(fake,{mcpUrl:'https://example.test/mcp',expectedFileId:'expected'});
    await gateway.discover();
    await expect(gateway.inspectTarget()).rejects.toThrow('TARGET_ERROR');
  });
});
