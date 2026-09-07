import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { designAgentConfigSchema, themeSchema, type DesignAgentProject, type DesignBrief } from './schema.js';

const REQUIRED_HEADINGS=['## Context','## Objective','## Inputs','## Constraints','## Acceptance Criteria'];
const SECRET_PATTERN=/(userToken=|PENPOT_MCP_URL|OPENAI_API_KEY|sk-[A-Za-z0-9_-]+)/;

function meta(markdown:string,key:string):string {
  const match=markdown.match(new RegExp(`^${key}:\\s*(.+)$`,'mi'));
  if(!match) throw new Error(`DESIGN_BRIEF_ERROR: missing ${key}`);
  return match[1].trim();
}

function validateMarkdown(markdown:string,file:string):void {
  if(SECRET_PATTERN.test(markdown)) throw new Error(`DESIGN_SECRET_ERROR: secret-like value found in ${file}`);
  for(const heading of REQUIRED_HEADINGS) if(!markdown.includes(heading)) throw new Error(`DESIGN_BRIEF_ERROR: ${file} missing ${heading}`);
}

function parseBrief(id:string,markdown:string,relativePath:string,allowedThemes:string[]):DesignBrief {
  validateMarkdown(markdown,relativePath);
  const workflow=meta(markdown,'Workflow');
  if(workflow!=='brief-to-screen') throw new Error(`DESIGN_BRIEF_ERROR: unsupported workflow ${workflow}`);
  const viewport=meta(markdown,'Viewport');
  if(!/^\d+x\d+$/.test(viewport)) throw new Error(`DESIGN_BRIEF_ERROR: invalid viewport ${viewport}`);
  const theme=themeSchema.parse(meta(markdown,'Theme'));
  if(!allowedThemes.includes(theme)) throw new Error(`DESIGN_BRIEF_ERROR: theme ${theme} is not allowed`);
  const screen=meta(markdown,'Screen');
  if(screen!==id) throw new Error(`DESIGN_BRIEF_ERROR: Screen ${screen} does not match filename ${id}`);
  return {id,workflow,viewport,theme,markdown,relativePath};
}

export async function loadDesignAgent(rootDir:string):Promise<DesignAgentProject> {
  const configPath='design-agent/config.json';
  const configRaw=await readFile(path.join(rootDir,configPath),'utf8');
  if(SECRET_PATTERN.test(configRaw)) throw new Error('DESIGN_SECRET_ERROR: secret-like value found in config');
  const config=designAgentConfigSchema.parse(JSON.parse(configRaw));
  const briefsDir=path.join(rootDir,'design-agent/briefs');
  const names=(await readdir(briefsDir)).filter(name=>name.endsWith('.md') && !name.startsWith('_')).sort();
  const briefs=new Map<string,DesignBrief>();
  for(const name of names) {
    const id=name.slice(0,-3);
    const relativePath=`design-agent/briefs/${name}`;
    const markdown=await readFile(path.join(rootDir,relativePath),'utf8');
    briefs.set(id,parseBrief(id,markdown,relativePath,config.allowedThemes));
  }
  if(!briefs.size) throw new Error('DESIGN_BRIEF_ERROR: no production briefs found');
  return {rootDir,config,configRaw,configPath,briefs};
}
