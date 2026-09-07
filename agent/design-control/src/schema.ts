import { z } from 'zod';

export const checkpointSchema=z.enum(['direction-approval','design-quality','accessibility','visual-approval']);
export const themeSchema=z.enum(['theme-a-green','theme-b-blue']);

export const designAgentConfigSchema=z.object({
  version:z.literal('v1'),
  provider:z.literal('penpot-ai-kit'),
  defaultWorkflow:z.literal('brief-to-screen'),
  requiredCheckpoints:z.array(checkpointSchema).min(1),
  allowedThemes:z.array(themeSchema).min(1),
  preferredViewport:z.string().regex(/^\d+x\d+$/),
  upstream:z.object({
    repository:z.literal('penpot/penpot-ai-kit'),
    mode:z.literal('external')
  })
});

export type DesignAgentConfig=z.infer<typeof designAgentConfigSchema>;

export type DesignBrief={
  id:string;
  workflow:'brief-to-screen';
  viewport:string;
  theme:z.infer<typeof themeSchema>;
  markdown:string;
  relativePath:string;
};

export type DesignAgentProject={
  rootDir:string;
  config:DesignAgentConfig;
  configRaw:string;
  configPath:string;
  briefs:Map<string,DesignBrief>;
};
