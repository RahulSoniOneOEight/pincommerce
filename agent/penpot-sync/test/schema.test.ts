import { describe, expect, it } from 'vitest';
import { ProjectDefinitionSchema } from '../src/schema.js';

const base = {
  foundations:{typography:{x:1},spacing:{x:1},radius:{x:1},shadow:{x:'s'},grid:{x:1}},
  themes:[
    {id:'a',name:'A',colors:{primary:'1',primaryForeground:'1',background:'1',surface:'1',surfaceMuted:'1',text:'1',textMuted:'1',border:'1',accent:'1',accentForeground:'1'},decoration:{watermarkOpacity:0,motifs:[]}},
    {id:'b',name:'B',colors:{primary:'1',primaryForeground:'1',background:'1',surface:'1',surfaceMuted:'1',text:'1',textMuted:'1',border:'1',accent:'1',accentForeground:'1'},decoration:{watermarkOpacity:.03,motifs:['technical-lines']}}
  ],
  components:[{id:'button',variants:['primary']}],
  b2cScreens:[{id:'b2c-home',components:['button']}],
  b2bScreens:[{id:'b2b-home',components:['button']}],
  routes:[{id:'r1',flow:'b2c',from:'b2c-home',to:'b2c-home'}]
} as const;

describe('project schema', () => {
  it('accepts valid project', () => expect(ProjectDefinitionSchema.safeParse(base).success).toBe(true));
  it('rejects duplicate component ids', () => expect(ProjectDefinitionSchema.safeParse({...base,components:[...base.components,{id:'button',variants:['x']}]}).success).toBe(false));
  it('rejects unknown screen components', () => expect(ProjectDefinitionSchema.safeParse({...base,b2cScreens:[{id:'b2c-home',components:['missing']}]}).success).toBe(false));
  it('rejects duplicate screen ids', () => expect(ProjectDefinitionSchema.safeParse({...base,b2bScreens:[{id:'b2c-home',components:['button']}]}).success).toBe(false));
  it('rejects unknown route targets', () => expect(ProjectDefinitionSchema.safeParse({...base,routes:[{id:'r1',flow:'b2c',from:'b2c-home',to:'missing'}]}).success).toBe(false));
});
