import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const base = process.env.STORYBOOK_URL || "http://127.0.0.1:6006";
const outDir = process.env.EVIDENCE_DIR || "artifacts/design-evidence";
const cases = [
  ["product-card", "commerce-productcard--default"],
  ["category-rail", "commerce-categoryrail--default"],
  ["b2b-quick-order", "commerce-b2bquickorder--default"],
  ["dashboard-kpi", "commerce-dashboardkpi--default"],
  ["exception-table", "commerce-exceptiontable--default"],
  ["filter-bar", "commerce-filterbar--default"],
  ["checkout-summary", "commerce-checkoutsummary--default"],
  ["navigation-menu", "commerce-navigationmenu--default"],
  ["form-section", "commerce-formsection--default"],
];
const viewports = {
  "mobile-390": { width: 390, height: 844 },
  "tablet-768": { width: 768, height: 1024 },
  "desktop-1440": { width: 1440, height: 1000 },
};

await fs.mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const captures = [];

for (const [pattern, storyId] of cases) {
  for (const [viewportId, viewport] of Object.entries(viewports)) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    const url = `${base}/iframe.html?id=${storyId}&viewMode=story`;
    await page.goto(url, { waitUntil: "networkidle" });
    const file = `${pattern}__${viewportId}.png`;
    const filePath = path.join(outDir, file);
    await page.screenshot({ path: filePath, fullPage: true });

    const png = await fs.readFile(filePath);
    const screenshotSha = "sha256:" + crypto.createHash("sha256").update(png).digest("hex");
    const domSnapshot = await page.evaluate(() => {
      const root = document.body;
      const styles = [...document.querySelectorAll("button,table,article,nav,[role]")].map((el) => {
        const s = getComputedStyle(el);
        return {
          tag: el.tagName,
          role: el.getAttribute("role"),
          aria: el.getAttribute("aria-label"),
          text: (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 300),
          display: s.display,
          color: s.color,
          backgroundColor: s.backgroundColor,
          fontSize: s.fontSize,
          borderRadius: s.borderRadius,
        };
      });
      return { html: root.innerHTML.replace(/\s+/g, " ").trim(), styles };
    });
    const domFingerprint = "sha256:" + crypto.createHash("sha256").update(JSON.stringify(domSnapshot)).digest("hex");

    const axe = await new AxeBuilder({ page }).analyze();
    const impact = { critical: 0, serious: 0, moderate: 0, minor: 0 };
    for (const violation of axe.violations) {
      if (violation.impact && impact[violation.impact] !== undefined) impact[violation.impact] += 1;
    }

    const interaction = await page.evaluate(() => {
      const nodes = [...document.querySelectorAll("button,a[href],input,select,textarea,[role='button'],[tabindex]")];
      const unlabeled = nodes.filter((el) => {
        const label = el.getAttribute("aria-label") || el.getAttribute("title") || (el.textContent || "").trim();
        const labelledBy = el.getAttribute("aria-labelledby");
        const id = el.getAttribute("id");
        const explicitLabel = id ? document.querySelector('label[for="' + CSS.escape(id) + '"]') : null;
        const wrappingLabel = el.closest("label");
        return !label && !labelledBy && !explicitLabel && !wrappingLabel;
      }).length;
      const focusable = nodes.filter((el) => !el.hasAttribute("disabled") && el.getAttribute("tabindex") !== "-1").length;
      return { interactive_count: nodes.length, unlabeled_interactive: unlabeled, focusable_interactive: focusable };
    });

    const perf = await page.evaluate(() => {
      const nav = performance.getEntriesByType("navigation")[0];
      const resources = performance.getEntriesByType("resource");
      return {
        dom_content_loaded_ms: nav ? nav.domContentLoadedEventEnd : 0,
        transfer_bytes: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
      };
    });

    captures.push({
      pattern,
      story_id: storyId,
      viewport_id: viewportId,
      width: viewport.width,
      height: viewport.height,
      file,
      screenshot_sha256: screenshotSha,
      dom_fingerprint: domFingerprint,
      accessibility: { ...impact, ...interaction },
      performance: perf,
    });
    await context.close();
  }
}

await browser.close();
const result = { generated_at: new Date().toISOString(), captures };
await fs.writeFile(path.join(outDir, "evidence.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result));
