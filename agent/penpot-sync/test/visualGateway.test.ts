import { describe, expect, it } from 'vitest';
import { PenpotMcpGateway } from '../src/mcp/gateway.js';
import { FakeMcpTransport, mcpText } from './fakes/fakeMcp.js';

const config:any={mcpUrl:'https://design.penpot.app/mcp/stream?userToken=secret'};
const target:any={repoId:'screen:b2c-home',targetKind:'screen',renderVersion:'v1',fingerprint:'fp1',tree:{id:'root',type:'frame',width:390,height:844,children:[]}};

describe('PenpotMcpGateway visual rendering',()=>{
  it('renders into existing root and writes the fingerprint to registry',async()=>{
    const fake=new FakeMcpTransport(undefined,()=>mcpText(true));
    const gateway=new PenpotMcpGateway(fake,config);
    await gateway.renderVisual(target,{repoId:target.repoId,remoteId:'screen-root',kind:'ensure-screen',payload:{}} as any);
    const code=fake.calls.map(x=>String(x.args.code||'')).join('\n');
    expect(code).toContain('screen-root');
    expect(code).toContain('fp1');
    expect(fake.calls).toHaveLength(2);
  });
  it('refuses a missing managed root id',async()=>{
    const fake=new FakeMcpTransport();
    const gateway=new PenpotMcpGateway(fake,config);
    await expect(gateway.renderVisual(target,{repoId:target.repoId,remoteId:'',kind:'ensure-screen'} as any)).rejects.toThrow('VISUAL_TARGET_ERROR');
  });
});
