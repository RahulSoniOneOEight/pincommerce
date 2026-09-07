import type { DesignAgentProject } from './schema.js';

function displayTheme(theme:string):string {
  return theme==='theme-b-blue' ? 'Theme B — Premium Blue' : 'Theme A — BuildKart Green';
}

export function buildHandoff(project:DesignAgentProject,screenId:string):string {
  const brief=project.briefs.get(screenId);
  if(!brief) throw new Error(`DESIGN_HANDOFF_ERROR: unknown screen ${screenId}`);
  const checkpoints=project.config.requiredCheckpoints.map(x=>`- ${x}`).join('\n');
  return `# PinCommerce → Penpot AI Kit Handoff\n\n`+
    `## Purpose\nBuild and review the **${screenId}** screen in the currently connected Penpot file using the upstream **penpot/penpot-ai-kit** workflow layer. The repository brief is the product/design contract; Penpot is the editable visual workspace.\n\n`+
    `## Workflow\n- Workflow: ${brief.workflow}\n- Viewport: ${brief.viewport}\n- Theme: ${displayTheme(brief.theme)}\n- Use upstream Penpot AI Kit externally; do not vendor or rewrite its skills in this project.\n\n`+
    `## Operator preflight\n1. Open the intended Penpot file and keep the target page active.\n2. In Penpot, connect **File → MCP Server → Connect**.\n3. Run \`npm run penpot:check\` and confirm the expected file/page before any canvas mutation.\n4. Inspect existing tokens, components and screen patterns before proposing changes.\n\n`+
    `## Required checkpoints\n${checkpoints}\n\n`+
    `Before meaningful canvas changes, propose the visual direction and wait for direction approval. Build section-by-section. After composition, run design-quality and accessibility review. Do not call the design approved until the user visually reviews the actual Penpot result.\n\n`+
    `## Screen brief\n\n${brief.markdown.trim()}\n\n`+
    `## Implementation rules\n- Prefer existing semantic tokens and reusable components over hardcoded values.\n- Keep all output Penpot-native and editable.\n- Do not expose MCP keys, access tokens or credential-bearing URLs in notes, layers, output or logs.\n- Preserve the PinCommerce control-plane constraints even when proposing aesthetic improvements.\n\n`+
    `## Completion output\nReturn: (1) a concise summary of sections created/changed, (2) design-quality review result, (3) accessibility findings/fixes, (4) any intentional deviations from the brief, and (5) request for visual approval.\n`;
}
