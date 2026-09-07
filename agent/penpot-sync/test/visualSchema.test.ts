import { describe, expect, it } from 'vitest';
import { VisualProjectInputSchema } from '../src/visual/schema.js';

describe('VisualProjectInputSchema', () => {
  it('accepts Theme B visual state and rejects external image URLs', () => {
    const parsed = VisualProjectInputSchema.parse({
      theme: { id:'theme-b', canvas:{width:390,height:844}, colors:{primary:'#173B72',primaryForeground:'#FFFFFF',background:'#F6F8FC',surface:'#FFFFFF',text:'#111827',textMuted:'#637083',border:'#DCE4F0',accent:'#C99745'}, spacing:{xs:4,sm:8,md:12,lg:16,xl:20,xxl:24}, radius:{sm:8,md:12,lg:16}, watermarkOpacity:0.03 },
      components:[{id:'button',variants:['primary'],root:{id:'root',type:'frame',width:120,height:44,children:[]}}],
      assets:[{id:'category-plumbing',kind:'category-icon',recipe:'plumbing'}],
      screens:[{id:'b2c-home',title:'Home',sections:[]}]
    });
    expect(parsed.theme.id).toBe('theme-b');
    expect(() => VisualProjectInputSchema.parse({...parsed, assets:[{id:'remote',kind:'image',url:'https://example.com/x.png'}]})).toThrow();
  });
});
