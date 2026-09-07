import fs from 'node:fs/promises';
import path from 'node:path';
import { VisualProjectInputSchema, type RenderNode, type VisualProjectInput } from './schema.js';

async function readJson(file: string): Promise<any> {
  return JSON.parse(await fs.readFile(file, 'utf8'));
}

function walk(node: RenderNode, visit: (node: RenderNode)=>void) {
  visit(node);
  if (node.type === 'frame') for (const child of node.children) walk(child, visit);
}

export async function loadVisualProject(root: string): Promise<VisualProjectInput> {
  try {
    const [theme, componentsDoc, assetsDoc, screensDoc, catalog, b2c] = await Promise.all([
      readJson(path.join(root,'design-system/visual/theme-b.json')),
      readJson(path.join(root,'design-system/visual/components.json')),
      readJson(path.join(root,'design-system/visual/assets.json')),
      readJson(path.join(root,'screens/b2c/visual-v1.json')),
      readJson(path.join(root,'design-system/components/catalog.json')),
      readJson(path.join(root,'screens/b2c/screens.json'))
    ]);
    const parsed = VisualProjectInputSchema.parse({theme,components:componentsDoc.components,assets:assetsDoc.assets,screens:screensDoc.screens});
    const knownComponents = new Set((catalog.components ?? []).map((x:any)=>x.id));
    const knownScreens = new Set((b2c.screens ?? []).map((x:any)=>x.id));
    for (const component of parsed.components) {
      if (!knownComponents.has(component.id)) throw new Error(`component ${component.id} is not in catalog`);
      walk(component.root, node => {
        if (node.type === 'component-instance' && !knownComponents.has(node.componentId)) throw new Error(`component ${component.id} references unknown component ${node.componentId}`);
      });
    }
    for (const screen of parsed.screens) {
      if (!knownScreens.has(screen.id)) throw new Error(`screen ${screen.id} is not in B2C manifest`);
      for (const section of screen.sections) walk(section.root, node => {
        if (node.type === 'component-instance' && !knownComponents.has(node.componentId)) throw new Error(`screen ${screen.id} references unknown component ${node.componentId}`);
      });
    }
    return parsed;
  } catch (error) {
    if (error instanceof Error && error.message.startsWith('VISUAL_VALIDATION_ERROR:')) throw error;
    throw new Error(`VISUAL_VALIDATION_ERROR: ${error instanceof Error ? error.message : String(error)}`);
  }
}
