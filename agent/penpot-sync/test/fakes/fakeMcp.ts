import type { McpTool, McpTransport } from '../../src/mcp/types.js';

export class FakeMcpTransport implements McpTransport {
  calls: Array<{name:string;args:Record<string,unknown>}> = [];
  connected = false;
  listCount = 0;
  constructor(public tools: McpTool[] = [{name:'execute_code'}], private handler: (name:string,args:Record<string,unknown>)=>unknown = ()=>({content:[{type:'text',text:'{}'}]})) {}
  async connect(){ this.connected = true; }
  async listTools(){ this.listCount++; return this.tools; }
  async callTool(name:string,args:Record<string,unknown>){ this.calls.push({name,args}); return this.handler(name,args); }
  async close(){ this.connected = false; }
}

export function mcpText(result: unknown) { return { content: [{ type:'text', text: JSON.stringify({result}) }] }; }
