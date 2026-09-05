import { z } from 'zod';

export const ThemeSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  colors: z.object({
    primary: z.string(), primaryForeground: z.string(), background: z.string(), surface: z.string(),
    surfaceMuted: z.string(), text: z.string(), textMuted: z.string(), border: z.string(), accent: z.string(), accentForeground: z.string()
  }),
  decoration: z.object({ watermarkOpacity: z.number().min(0).max(1), motifs: z.array(z.string()) })
});

export const FoundationsSchema = z.object({
  typography: z.record(z.any()), spacing: z.record(z.number()), radius: z.record(z.number()), shadow: z.record(z.string()), grid: z.record(z.number())
});

export const ComponentSchema = z.object({ id: z.string().min(1), variants: z.array(z.string()).min(1) });
export const ScreenSchema = z.object({ id: z.string().min(1), components: z.array(z.string()).min(1) });
export const RouteSchema = z.object({ id: z.string().min(1), flow: z.enum(['b2c','b2b']), from: z.string(), to: z.string() });

export const ProjectDefinitionSchema = z.object({
  foundations: FoundationsSchema,
  themes: z.tuple([ThemeSchema, ThemeSchema]),
  components: z.array(ComponentSchema),
  b2cScreens: z.array(ScreenSchema),
  b2bScreens: z.array(ScreenSchema),
  routes: z.array(RouteSchema)
}).superRefine((project, ctx) => {
  const componentIds = project.components.map(c => c.id);
  if (new Set(componentIds).size !== componentIds.length) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'duplicate component IDs' });
  const allScreens = [...project.b2cScreens, ...project.b2bScreens];
  const screenIds = allScreens.map(s => s.id);
  if (new Set(screenIds).size !== screenIds.length) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'duplicate screen IDs' });
  const componentSet = new Set(componentIds);
  for (const screen of allScreens) for (const id of screen.components) if (!componentSet.has(id)) ctx.addIssue({ code: z.ZodIssueCode.custom, message: `unknown component ${id} in ${screen.id}` });
  const screenSet = new Set(screenIds);
  for (const route of project.routes) {
    if (!screenSet.has(route.from)) ctx.addIssue({ code: z.ZodIssueCode.custom, message: `unknown route source ${route.from}` });
    if (!screenSet.has(route.to)) ctx.addIssue({ code: z.ZodIssueCode.custom, message: `unknown route target ${route.to}` });
  }
});

export type ProjectDefinition = z.infer<typeof ProjectDefinitionSchema>;
