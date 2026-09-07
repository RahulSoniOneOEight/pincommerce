import { createHash } from 'node:crypto';
import type { DesignAgentProject } from './schema.js';

export type DesignRunManifest={
  version:'v1';
  screenId:string;
  workflow:'brief-to-screen';
  viewport:string;
  theme:string;
  briefSha256:string;
  configSha256:string;
  requiredCheckpoints:string[];
  inputs:{config:string;brief:string};
};

function sha256(value:string):string {
  return createHash('sha256').update(value,'utf8').digest('hex');
}

function normalize(value:unknown):unknown {
  if(Array.isArray(value)) return value.map(normalize);
  if(value && typeof value==='object') return Object.fromEntries(Object.entries(value as Record<string,unknown>).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,normalize(v)]));
  return value;
}

export function stableManifestJson(manifest:DesignRunManifest):string {
  return JSON.stringify(normalize(manifest),null,2)+'\n';
}

export function buildRunManifest(project:DesignAgentProject,screenId:string):DesignRunManifest {
  const brief=project.briefs.get(screenId);
  if(!brief) throw new Error(`DESIGN_MANIFEST_ERROR: unknown screen ${screenId}`);
  const canonicalConfig=JSON.stringify(normalize(project.config));
  return {
    version:'v1',
    screenId,
    workflow:brief.workflow,
    viewport:brief.viewport,
    theme:brief.theme,
    briefSha256:sha256(brief.markdown),
    configSha256:sha256(canonicalConfig),
    requiredCheckpoints:[...project.config.requiredCheckpoints],
    inputs:{config:project.configPath,brief:brief.relativePath}
  };
}
