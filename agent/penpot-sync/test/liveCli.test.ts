import { describe, expect, it } from 'vitest';
import { runLive } from '../src/liveCli.js';
import { FakeMcpTransport, mcpText } from './fakes/fakeMcp.js';

function fake() {
  return new FakeMcpTransport(undefined,(_name,args)=>{
    const code=String(args.code||'');
    if(code.includes('currentFile?.id')) return mcpText({fileId:'f1',fileName:'Demo',pageId:'p1',pageName:'Page 1'});
    if(code.includes('getPluginData')) return mcpText([]);
    return mcpText({remoteId:'r1'});
  });
}
const env={PENPOT_MCP_URL:'https://design.penpot.app/mcp/stream?userToken=supersecret'} as NodeJS.ProcessEnv;

describe('live CLI',()=>{
  it('check connects without design writes',async()=>{
    const transport=fake(); const logs:string[]=[];
    expect(await runLive(['check'],process.cwd(),{transport,env,log:x=>logs.push(x),error:()=>{}})).toBe(0);
    expect(transport.calls.some(c=>String(c.args.code||'').includes('createBoard'))).toBe(false);
    expect(logs.join('')).not.toContain('supersecret');
  });
  it('plan is read only',async()=>{
    const transport=fake();
    expect(await runLive(['plan'],process.cwd(),{transport,env,log:()=>{},error:()=>{}})).toBe(0);
    expect(transport.calls.some(c=>String(c.args.code||'').includes('createBoard'))).toBe(false);
  });
  it('sync refuses without --apply before connecting',async()=>{
    const transport=fake();
    expect(await runLive(['sync'],process.cwd(),{transport,env,log:()=>{},error:()=>{}})).toBe(2);
    expect(transport.connected).toBe(false);
  });
  it('verify reports drift without writing',async()=>{
    const transport=fake();
    expect(await runLive(['verify'],process.cwd(),{transport,env,log:()=>{},error:()=>{}})).toBe(1);
    expect(transport.calls.some(c=>String(c.args.code||'').includes('createBoard'))).toBe(false);
  });
});
