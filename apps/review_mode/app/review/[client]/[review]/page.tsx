import fs from "node:fs";
import path from "node:path";
import { parse } from "yaml";

type ReviewArtifact = {
  artifact_id: string;
  surface: string;
  route_or_screen?: string;
  environment: string;
  build_identity: string;
  journey?: string;
  viewport?: string;
  preview_url?: string;
  screenshot_ref?: string;
  approval_status: string;
};

type ReviewSession = {
  review_id: string;
  client_id: string;
  build_id: string;
  direction_id: string;
  artifacts: ReviewArtifact[];
  status: string;
};

type LiveEdit = {
  edit_id: string;
  category: string;
  summary: string;
  classification: string;
  route: string;
  status: string;
};

type LiveReviewSession = {
  session_id: string;
  review_id: string;
  source_build_id: string;
  tool: "nowa";
  edits: LiveEdit[];
  resulting_revision?: string | null;
  status: string;
};

function loadReview(client: string, review: string): ReviewSession {
  const file = path.resolve(
    process.cwd(),
    "../../client-projects",
    client,
    "feedback",
    `${review}.yaml`,
  );
  if (!fs.existsSync(file)) {
    throw new Error(`Review session not found: ${review}`);
  }
  return parse(fs.readFileSync(file, "utf8")) as ReviewSession;
}

function loadLiveReviewSessions(client: string, reviewId: string): LiveReviewSession[] {
  const feedbackDir = path.resolve(process.cwd(), "../../client-projects", client, "feedback");
  if (!fs.existsSync(feedbackDir)) return [];
  return fs.readdirSync(feedbackDir)
    .filter((name) => name.startsWith("LIVE-") && name.endsWith(".yaml"))
    .map((name) => parse(fs.readFileSync(path.join(feedbackDir, name), "utf8")) as LiveReviewSession)
    .filter((item) => item.review_id === reviewId && item.tool === "nowa");
}

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ client: string; review: string }>;
}) {
  const { client, review } = await params;
  const session = loadReview(client, review);
  const liveSessions = loadLiveReviewSessions(client, session.review_id);

  return (
    <main className="agency-page review-page">
      <header className="review-header">
        <div>
          <p className="eyebrow">Review Mode</p>
          <h1>{session.direction_id}</h1>
          <p>{session.build_id}</p>
        </div>
        <span className="status-chip">{session.status}</span>
      </header>

      {liveSessions.length > 0 && (
        <section>
          <h2>Live client review</h2>
          <div className="review-grid">
            {liveSessions.map((live) => (
              <article className="agency-card review-card" key={live.session_id}>
                <div className="artifact-meta">
                  <strong>Nowa</strong>
                  <span>{live.status}</span>
                </div>
                <p>{live.session_id}</p>
                <small>Source build: {live.source_build_id}</small>
                <small>Resulting revision: {live.resulting_revision || "QA / source sync pending"}</small>
                <ul>
                  {live.edits.map((edit) => (
                    <li key={edit.edit_id}>
                      <strong>{edit.category}</strong>: {edit.summary} — {edit.classification} / {edit.status}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="review-grid">
        {session.artifacts.map((artifact) => (
          <article className="agency-card review-card" key={artifact.artifact_id}>
            <div className="artifact-meta">
              <strong>{artifact.surface}</strong>
              <span>{artifact.viewport || "default"}</span>
            </div>
            <p>{artifact.route_or_screen || artifact.journey || "Review artifact"}</p>
            <code>{artifact.screenshot_ref || "Screenshot pending"}</code>
            <div className="review-actions">
              <button type="button">Approve</button>
              <button type="button">Request changes</button>
            </div>
            <small>
              UI actions are review affordances; repository decisions are persisted
              through governed Review/BugDrop tooling.
            </small>
          </article>
        ))}
      </section>
    </main>
  );
}
