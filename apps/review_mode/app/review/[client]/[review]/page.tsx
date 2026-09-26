import fs from "node:fs";
import path from "node:path";
import { parse } from "yaml";

type AnyDoc = Record<string, any>;
type ReviewArtifact = {
  artifact_id: string; surface: string; route_or_screen?: string; environment: string;
  build_identity: string; journey?: string; viewport?: string; preview_url?: string;
  screenshot_ref?: string; approval_status: string;
};
type ReviewSession = { review_id:string; client_id:string; build_id:string; direction_id:string; artifacts:ReviewArtifact[]; status:string };

function projectRoot(client:string) {
  return path.resolve(process.cwd(), "../../client-projects", client);
}
function loadYaml(file:string):AnyDoc|null {
  if (!fs.existsSync(file)) return null;
  const value=parse(fs.readFileSync(file,"utf8"));
  return value && typeof value==="object" ? value as AnyDoc : null;
}
function loadReview(client:string, review:string):ReviewSession {
  const value=loadYaml(path.join(projectRoot(client),"feedback",review+".yaml"));
  if(!value) throw new Error(`Review session not found: ${review}`);
  return value as ReviewSession;
}
function latestYaml(dir:string, prefix=""):AnyDoc|null {
  if(!fs.existsSync(dir)) return null;
  const files=fs.readdirSync(dir).filter(x=>x.endsWith(".yaml")&&x.startsWith(prefix)).sort();
  return files.length ? loadYaml(path.join(dir,files[files.length-1])) : null;
}
function bySurface(artifacts:ReviewArtifact[]) {
  return artifacts.reduce<Record<string,ReviewArtifact[]>>((acc,a)=>{(acc[a.surface]??=[]).push(a);return acc;},{});
}
function coverage(artifacts:ReviewArtifact[], required:string[]) {
  return required.map(surface=>({surface,count:artifacts.filter(x=>x.surface===surface).length,complete:artifacts.some(x=>x.surface===surface&&Boolean(x.screenshot_ref||x.preview_url))}));
}

export default async function ReviewPage({params}:{params:Promise<{client:string;review:string}>}) {
  const {client,review}=await params;
  const root=projectRoot(client);
  const session=loadReview(client,review);
  const pkg=latestYaml(path.join(root,"experience","review"),"DRP-");
  const strategy=loadYaml(path.join(root,"experience","strategy.yaml"));
  const synthesis=loadYaml(path.join(root,"experience","synthesis.yaml"));
  const theme=loadYaml(path.join(root,"experience","design","theme-resolution.yaml"));
  const components=loadYaml(path.join(root,"experience","design","component-contract-registry.yaml"));
  const masterDesign=loadYaml(path.join(root,"experience","design","master-design-system.yaml"));
  const implementationRegistry=loadYaml(path.join(root,"experience","design","ui-implementation-registry.yaml"));
  const iconRegistry=loadYaml(path.join(root,"experience","design","icon-registry.yaml"));
  const motionRegistry=loadYaml(path.join(root,"experience","design","motion-registry.yaml"));
  const designIr=loadYaml(path.join(root,"experience","design","design-ir.yaml"));
  const journeys=loadYaml(path.join(root,"derived","journey-graph.yaml"));
  const refs=loadYaml(path.join(root,"experience","references","adaptation.yaml"));
  const selection=loadYaml(path.join(root,"experience","design","selection.yaml"));
  const grouped=bySurface(session.artifacts||[]);
  const required=(pkg?.surface_refs||Object.keys(grouped)) as string[];
  const matrix=coverage(session.artifacts||[],required);
  const directions=["a","b","c"].map(id=>loadYaml(path.join(root,"experience","directions",id+".yaml"))).filter(Boolean) as AnyDoc[];
  const states=Array.from(new Set((designIr?.journeys||[]).flatMap((j:any)=>(j.nodes||[]).flatMap((n:any)=>n.state_refs||[])))) as string[];
  const viewports=Array.from(new Set((session.artifacts||[]).map(x=>x.viewport||"default")));
  const designRevision=pkg?.design_revision||"not packaged";

  return <main className="agency-page review-page">
    <header className="review-header">
      <div><p className="eyebrow">PinCommerce Experience Review</p><h1>{client} · {session.direction_id}</h1><p>Build {session.build_id} · Design {designRevision}</p></div>
      <span className="status-chip">{session.status}</span>
    </header>

    <nav className="review-tabs" aria-label="Review sections">
      {["overview","directions","design-system","screens","journeys","responsive-states","references","qa","feedback","approval"].map(x=><a key={x} href={"#"+x}>{x.replace("-"," ")}</a>)}
    </nav>

    <section id="overview" className="review-section">
      <h2>Experience overview</h2>
      <div className="summary-grid">
        <article className="agency-card"><h3>Goals & principles</h3><ul>{(synthesis?.principles||strategy?.principles||[]).map((x:string)=><li key={x}>{x}</li>)}</ul></article>
        <article className="agency-card"><h3>Users & surfaces</h3><p>{required.join(" · ")||"No required surfaces recorded"}</p><p>{(journeys?.journeys||[]).map((x:any)=>x.actor).filter((x:string,i:number,a:string[])=>a.indexOf(x)===i).join(" · ")}</p></article>
        <article className="agency-card"><h3>Key journeys</h3><ul>{(journeys?.journeys||[]).map((x:any)=><li key={x.id}>{x.id} — {(x.surfaces||[]).join(" → ")}</li>)}</ul></article>
        <article className="agency-card"><h3>Decision baseline</h3><p>Direction: {session.direction_id}</p><p>Penpot: {pkg?.penpot_ref||"required"}</p><p>Source revision: {pkg?.source_revision||"not packaged"}</p></article>
      </div>
    </section>

    <section id="directions" className="review-section">
      <h2>A / B / C directions</h2>
      <div className="direction-grid">{directions.map((d:any)=><article className="agency-card" key={d.direction_id}><div className="artifact-meta"><strong>{d.direction_id}</strong><span>{d.status}</span></div><h3>{d.strategy}</h3><p>{(d.differentiators||[]).join(" · ")}</p><p><strong>Journey emphasis</strong>: {(d.journey_emphasis||[]).join(", ")}</p><details><summary>Design intent</summary><pre>{JSON.stringify(d.design_intent||{},null,2)}</pre></details></article>)}</div>
      <p className="review-note">Selection or mixing must be persisted as a governed decision; visual comparison is advisory until the human decision is recorded.</p>
    </section>

    <section id="design-system" className="review-section">
      <div className="section-heading"><h2>Design system</h2>{pkg?.penpot_ref&&<span className="status-chip">Penpot {pkg.penpot_ref}</span>}</div>
      <div className="summary-grid">
        <article className="agency-card"><h3>Semantic colors</h3><div className="token-list">{Object.entries(theme?.semantic_roles||{}).map(([k,v])=><div className="token-row" key={k}><span>{k}</span><code>{String(v)}</code></div>)}</div></article>
        <article className="agency-card"><h3>Typography & imagery</h3><p>Fonts: {(theme?.overrides?.fonts||[]).join(", ")||"default tokens"}</p><p>Image direction: {(theme?.overrides?.image_direction||[]).join(", ")||"not specified"}</p><p>Motion: {theme?.overrides?.motion_preference||"balanced"}</p></article>
        <article className="agency-card"><h3>Master tokens</h3><p>{Object.keys(masterDesign?.tokens||{}).join(" · ")||"not materialized"}</p><p>Breakpoints: {Object.entries(masterDesign?.breakpoints||{}).map(([k,v])=>`${k}:${v}`).join(" · ")}</p></article><article className="agency-card"><h3>Icons & motion</h3><p>Icons: {iconRegistry?.policy ? `${iconRegistry.policy.primary} → ${iconRegistry.policy.secondary} → ${iconRegistry.policy.fallback}` : "not materialized"}</p><p>Motion contracts: {(motionRegistry?.motions||[]).length}</p></article><article className="agency-card wide"><h3>Components & implementation mapping</h3><div className="component-grid">{(implementationRegistry?.components||[]).map((m:any)=><div className="component-cell" key={m.semantic_id}><strong>{m.semantic_id}</strong><span>Penpot: {m.penpot?.component}</span><small>Flutter: {m.flutter?.owned_component} · {m.flutter?.primitive}</small><small>Web: {m.web?.owned_component} · {m.web?.primitive}</small></div>)}</div>{!implementationRegistry&&<div className="component-grid">{(components?.components||[]).map((x:any)=><div className="component-cell" key={x.id}><strong>{x.id}</strong><span>{(x.variants||[]).join(", ")}</span><small>{(x.states||[]).join(" · ")}</small></div>)}</div>}</article>
      </div>
    </section>

    <section id="screens" className="review-section">
      <h2>Screen gallery</h2>
      <div className="coverage-row">{matrix.map(x=><span className={"coverage-chip "+(x.complete?"ok":"missing")} key={x.surface}>{x.surface}: {x.count} {x.complete?"✓":"missing preview"}</span>)}</div>
      {Object.entries(grouped).map(([surface,items])=><div key={surface} className="surface-group"><h3>{surface}</h3><div className="review-grid">{items.map(a=><article className="agency-card review-card" key={a.artifact_id}><div className="artifact-meta"><strong>{a.route_or_screen||a.journey||a.artifact_id}</strong><span>{a.viewport||"default"}</span></div>{a.preview_url?<iframe title={a.artifact_id} src={a.preview_url}/>:a.screenshot_ref?<code>{a.screenshot_ref}</code>:<div className="missing-preview">Preview evidence missing</div>}<small>{a.journey||"No journey mapped"} · {a.approval_status}</small></article>)}</div></div>)}
    </section>

    <section id="journeys" className="review-section">
      <h2>Interactive journey review</h2>
      {(journeys?.journeys||[]).map((j:any)=><article className="agency-card journey-card" key={j.id}><div className="artifact-meta"><strong>{j.id}</strong><span>{j.actor}</span></div><p>{j.objective||""}</p><div className="journey-track">{(j.nodes||[]).map((n:any,i:number)=><details className="journey-node" key={n.id} open={i===0}><summary>{i+1}. {n.action} <small>{n.surface}</small></summary><p>Screen: {n.screen||"—"} · Capability: {n.capability||"—"}</p><p>Backend: {n.backend_operation||"—"} · Event: {n.event||"—"}</p><p>Success: {n.success_state} · Error: {n.error_state}</p><p>Next: {(n.next||[]).join(", ")||"complete"}</p>{n.handoff?.required&&<strong>Handoff: {n.handoff.from} → {n.handoff.to}</strong>}</details>)}</div></article>)}
    </section>

    <section id="responsive-states" className="review-section">
      <h2>Responsive & state matrix</h2>
      <div className="matrix-wrap"><table><thead><tr><th>Surface</th>{viewports.map(v=><th key={v}>{v}</th>)}</tr></thead><tbody>{required.map(s=><tr key={s}><th>{s}</th>{viewports.map(v=><td key={v}>{session.artifacts.some(a=>a.surface===s&&(a.viewport||"default")===v&&(a.screenshot_ref||a.preview_url))?"✓":"—"}</td>)}</tr>)}</tbody></table></div>
      <h3>Required states</h3><div className="coverage-row">{states.map(s=><span className="coverage-chip ok" key={s}>{s}</span>)}</div>
    </section>

    <section id="references" className="review-section">
      <h2>Reference adaptation</h2>
      {(refs?.sources||[]).map((s:any)=><article className="agency-card" key={s.source_id}><h3>{s.source_id}</h3><code>{s.ref}</code><div className="component-grid">{(s.patterns||[]).map((p:any)=><div className="component-cell" key={p.id}><strong>{p.id}</strong><span>{p.decision||"DECISION REQUIRED"}</span><small>{p.reason}</small><small>{(p.journeys||[]).join(", ")}</small></div>)}</div></article>)}
    </section>

    <section id="qa" className="review-section">
      <h2>QA & completeness</h2>
      <div className="summary-grid"><article className="agency-card"><h3>Review package</h3><p>{pkg?.status||"missing"}</p><p>{(pkg?.qa_refs||[]).length} QA evidence references</p></article><article className="agency-card"><h3>Selection</h3><p>{selection?.status||"missing"}</p><p>{selection?.preset||"No preset"}</p></article></div>
    </section>

    <section id="feedback" className="review-section">
      <h2>Feedback</h2>
      <p>Actions below write governed review evidence only when Review Mode write access is enabled.</p>
      <form className="decision-form" action="/api/review/decision" method="post">
        <input type="hidden" name="client" value={client}/><input type="hidden" name="review" value={session.review_id}/>
        <label>Reviewer <input name="reviewer" required/></label>
        <label>Role <select name="role" required><option value="reviewer">Reviewer</option><option value="approver">Approver</option><option value="admin">Admin</option></select></label>
        <label>Write token <input name="token" type="password" required/></label>
        <label>Surface <select name="surface" required>{required.map(s=><option key={s}>{s}</option>)}</select></label>
        <label>Journey <select name="journey"><option value="">—</option>{(journeys?.journeys||[]).map((j:any)=><option key={j.id}>{j.id}</option>)}</select></label>
        <label>Comment <textarea name="comment" required/></label>
        <div className="review-actions"><button name="action" value="approve">Approve target</button><button name="action" value="request-change">Request changes</button></div>
      </form>
    </section>

    <section id="approval" className="review-section">
      <h2>Experience decision</h2>
      <p>Final experience approval remains a hard human gate and is valid only after all required surfaces and journeys are approved, feedback is resolved, QA is recorded and the exact design/prototype revisions are bound.</p>
      <code>{pkg ? `Package ${pkg.package_id} · Penpot ${pkg.penpot_ref}` : "Review package not yet generated"}</code>
    </section>
  </main>;
}
