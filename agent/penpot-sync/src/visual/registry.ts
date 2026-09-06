export type VisualRegistryMeta = { version:'v1'; fingerprint:string };
export const VISUAL_RENDER_VERSION = 'v1' as const;
// Changes whenever renderer implementation semantics change without changing manifest shape.
// Including this in fingerprints forces a safe re-render of existing managed visual roots.
export const VISUAL_RENDER_BUILD = 'icon-container-1' as const;
