import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadProject } from './loadProject.js';
import { buildPlan } from './plan.js';

function valueFrom(argv: string[], flag: string): string | undefined {
  const i = argv.indexOf(flag);
  return i >= 0 ? argv[i + 1] : undefined;
}

export async function run(argv = process.argv.slice(2), root = process.cwd()): Promise<number> {
  const command = argv[0];
  try {
    const project = await loadProject(root);
    if (command === 'validate') {
      console.log(JSON.stringify({ valid: true, components: project.components.length, screens: project.b2cScreens.length + project.b2bScreens.length, routes: project.routes.length }));
      return 0;
    }
    if (command === 'sync:dry') {
      const plan = buildPlan(project);
      const output = JSON.stringify({ operationCount: plan.length, kinds: [...new Set(plan.map(x => x.kind))], operations: plan }, null, 2);
      const out = valueFrom(argv, '--out');
      if (out) {
        const target = path.resolve(root, out);
        await mkdir(path.dirname(target), { recursive: true });
        await writeFile(target, output, 'utf8');
      }
      console.log(output);
      return 0;
    }
    console.error('Usage: cli.ts validate | sync:dry [--out <path>]');
    return 2;
  } catch (error) {
    console.error((error as Error).message);
    return 1;
  }
}

const self = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(self)) process.exit(await run());
