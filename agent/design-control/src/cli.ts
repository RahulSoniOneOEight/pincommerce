import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadDesignAgent } from './loadDesignAgent.js';
import { buildHandoff } from './handoff.js';
import { buildRunManifest, stableManifestJson } from './runManifest.js';

function parseArgs(args:string[]):{command?:string;screen?:string;out?:string} {
  const [command,...rest]=args;
  const parsed:{command?:string;screen?:string;out?:string}={command};
  for(let i=0;i<rest.length;i++) {
    const token=rest[i];
    if(token==='--screen') {
      const value=rest[++i];
      if(!value) throw new Error('DESIGN_CLI_ERROR: --screen requires a value');
      parsed.screen=value;
    } else if(token==='--out') {
      const value=rest[++i];
      if(!value) throw new Error('DESIGN_CLI_ERROR: --out requires a value');
      parsed.out=value;
    } else {
      throw new Error(`DESIGN_CLI_ERROR: unknown argument ${token}`);
    }
  }
  return parsed;
}

export async function run(args:string[],rootDir=process.cwd()):Promise<number> {
  try {
    const {command,screen,out}=parseArgs(args);
    if(!command || !['validate','brief','run-manifest'].includes(command)) throw new Error(`DESIGN_CLI_ERROR: unknown command ${command??''}`);
    const project=await loadDesignAgent(rootDir);

    if(command==='validate') {
      console.log(JSON.stringify({valid:true,briefs:[...project.briefs.keys()].sort()}));
      return 0;
    }

    if(!screen) throw new Error(`DESIGN_CLI_ERROR: ${command} requires --screen`);

    if(command==='brief') {
      console.log(buildHandoff(project,screen));
      return 0;
    }

    if(!out) throw new Error('DESIGN_CLI_ERROR: run-manifest requires --out');
    const outputPath=path.isAbsolute(out)?out:path.join(rootDir,out);
    await mkdir(path.dirname(outputPath),{recursive:true});
    await writeFile(outputPath,stableManifestJson(buildRunManifest(project,screen)),'utf8');
    console.log(JSON.stringify({written:path.relative(rootDir,outputPath).replaceAll('\\','/'),screenId:screen}));
    return 0;
  } catch(error) {
    console.error(error instanceof Error ? error.message : String(error));
    return 1;
  }
}

const self=fileURLToPath(import.meta.url);
if(process.argv[1] && path.resolve(process.argv[1])===path.resolve(self)) process.exit(await run(process.argv.slice(2)));
