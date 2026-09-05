import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { ProjectDefinitionSchema, type ProjectDefinition } from './schema.js';

async function readJson(root: string, rel: string): Promise<any> {
  const file = path.join(root, rel);
  let text: string;
  try { text = await readFile(file, 'utf8'); } catch (error) { throw new Error(`Unable to read ${rel}: ${(error as Error).message}`); }
  try { return JSON.parse(text); } catch (error) { throw new Error(`Invalid JSON in ${rel}: ${(error as Error).message}`); }
}

export async function loadProject(rootDir: string): Promise<ProjectDefinition> {
  const [foundations, themeA, themeB, catalog, b2c, b2b, prototype] = await Promise.all([
    readJson(rootDir, 'design-system/tokens/foundations.json'),
    readJson(rootDir, 'design-system/tokens/theme-a-green.json'),
    readJson(rootDir, 'design-system/tokens/theme-b-blue.json'),
    readJson(rootDir, 'design-system/components/catalog.json'),
    readJson(rootDir, 'screens/b2c/screens.json'),
    readJson(rootDir, 'screens/b2b/screens.json'),
    readJson(rootDir, 'prototype/routes.json')
  ]);
  return ProjectDefinitionSchema.parse({ foundations, themes: [themeA, themeB], components: catalog.components, b2cScreens: b2c.screens, b2bScreens: b2b.screens, routes: prototype.routes });
}
