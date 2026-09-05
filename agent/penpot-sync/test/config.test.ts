import { describe, expect, it } from 'vitest';
import { loadPenpotConfig } from '../src/config.js';
import { redactUrl } from '../src/redact.js';

describe('Penpot config', () => {
  it('rejects missing PENPOT_MCP_URL', () => expect(() => loadPenpotConfig({})).toThrow('CONFIG_ERROR'));
  it('redacts userToken query values', () => expect(redactUrl('https://design.penpot.app/mcp/stream?userToken=secret123&x=1')).toBe('https://design.penpot.app/mcp/stream?userToken=%5BREDACTED%5D&x=1'));
  it('keeps optional file id', () => expect(loadPenpotConfig({PENPOT_MCP_URL:'https://example.test/mcp',PENPOT_FILE_ID:'file-1'}).expectedFileId).toBe('file-1'));
});
