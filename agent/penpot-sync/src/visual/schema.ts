import { z } from 'zod';

const HexSchema = z.string().regex(/^#[0-9A-Fa-f]{6}$/);
const TextRoleSchema = z.enum(['display','title','body','label','caption','price']);

export type RenderNode =
  | { id:string; type:'frame'; x?:number; y?:number; width:number; height:number; fill?:string; radius?:number; opacity?:number; children:RenderNode[] }
  | { id:string; type:'rect'; x:number; y:number; width:number; height:number; fill:string; radius?:number; opacity?:number }
  | { id:string; type:'text'; x:number; y:number; width?:number; text:string; role:'display'|'title'|'body'|'label'|'caption'|'price'; color?:string; size?:number; weight?:number; opacity?:number }
  | { id:string; type:'icon'; x:number; y:number; width:number; height:number; recipe:string; color?:string; opacity?:number }
  | { id:string; type:'component-instance'; x:number; y:number; componentId:string; variant?:string; props:Record<string,unknown> };

export const RenderNodeSchema: z.ZodType<RenderNode> = z.lazy(() => z.discriminatedUnion('type', [
  z.object({ id:z.string().min(1), type:z.literal('frame'), x:z.number().optional(), y:z.number().optional(), width:z.number().positive(), height:z.number().positive(), fill:HexSchema.optional(), radius:z.number().nonnegative().optional(), opacity:z.number().min(0).max(1).optional(), children:z.array(RenderNodeSchema).default([]) }),
  z.object({ id:z.string().min(1), type:z.literal('rect'), x:z.number(), y:z.number(), width:z.number().positive(), height:z.number().positive(), fill:HexSchema, radius:z.number().nonnegative().optional(), opacity:z.number().min(0).max(1).optional() }),
  z.object({ id:z.string().min(1), type:z.literal('text'), x:z.number(), y:z.number(), width:z.number().positive().optional(), text:z.string(), role:TextRoleSchema, color:HexSchema.optional(), size:z.number().positive().optional(), weight:z.number().min(100).max(900).optional(), opacity:z.number().min(0).max(1).optional() }),
  z.object({ id:z.string().min(1), type:z.literal('icon'), x:z.number(), y:z.number(), width:z.number().positive(), height:z.number().positive(), recipe:z.string().min(1), color:HexSchema.optional(), opacity:z.number().min(0).max(1).optional() }),
  z.object({ id:z.string().min(1), type:z.literal('component-instance'), x:z.number(), y:z.number(), componentId:z.string().min(1), variant:z.string().optional(), props:z.record(z.unknown()).default({}) })
]));

export const VisualThemeSchema = z.object({
  id:z.literal('theme-b'),
  canvas:z.object({width:z.literal(390),height:z.literal(844)}),
  colors:z.object({primary:HexSchema,primaryForeground:HexSchema,background:HexSchema,surface:HexSchema,text:HexSchema,textMuted:HexSchema,border:HexSchema,accent:HexSchema}),
  spacing:z.object({xs:z.number(),sm:z.number(),md:z.number(),lg:z.number(),xl:z.number(),xxl:z.number()}),
  radius:z.object({sm:z.number(),md:z.number(),lg:z.number()}),
  watermarkOpacity:z.number().min(0.02).max(0.04)
});

export const VisualComponentDefinitionSchema = z.object({id:z.string().min(1),variants:z.array(z.string()).min(1),root:RenderNodeSchema});
export const VisualAssetDefinitionSchema = z.object({id:z.string().min(1),kind:z.enum(['category-icon','product-placeholder']),recipe:z.string().min(1)}).strict();
export const VisualScreenDefinitionSchema = z.object({id:z.string().min(1),title:z.string(),sections:z.array(z.object({id:z.string().min(1),root:RenderNodeSchema}))});

export const VisualProjectInputSchema = z.object({
  theme: VisualThemeSchema,
  components: z.array(VisualComponentDefinitionSchema),
  assets: z.array(VisualAssetDefinitionSchema),
  screens: z.array(VisualScreenDefinitionSchema)
});

export type VisualTheme = z.infer<typeof VisualThemeSchema>;
export type VisualComponentDefinition = z.infer<typeof VisualComponentDefinitionSchema>;
export type VisualAssetDefinition = z.infer<typeof VisualAssetDefinitionSchema>;
export type VisualScreenDefinition = z.infer<typeof VisualScreenDefinitionSchema>;
export type VisualProjectInput = z.infer<typeof VisualProjectInputSchema>;
