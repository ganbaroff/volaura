/**
 * Screenshot batch for Ecosystem Redesign 2026-04-15 — P0.3.
 *
 * Runs public (no-auth) routes first × 2 viewports (desktop 1440, mobile 390).
 * Output: docs/design/ECOSYSTEM-REDESIGN-2026-04-15/screenshots/public/
 *
 * Usage:
 *   pnpm dlx playwright install chromium  # one-time
 *   VOLAURA_URL=https://volaura.app npx tsx scripts/screenshot-routes.ts
 *
 * Auth-gated routes require a signed-in state and will be batched separately
 * once a test user is seeded or an `E2E_TEST_SECRET` login flow is wired.
 */
import { chromium, type Browser, type Page } from "playwright";
import * as fs from "node:fs";
import * as path from "node:path";

const BASE_URL = process.env.VOLAURA_URL || "https://volaura.app";
const LOCALE = "az"; // primary locale
const OUT_DIR = path.resolve(
  __dirname,
  "..",
  "docs/design/ECOSYSTEM-REDESIGN-2026-04-15/screenshots/public",
);

type Route = { slug: string; path: string; note?: string };

/** Public (no-auth) routes. 13 × 2 viewports = 26 screenshots. */
const PUBLIC_ROUTES: Route[] = [
  { slug: "landing", path: `/${LOCALE}` },
  { slug: "login", path: `/${LOCALE}/login` },
  { slug: "signup", path: `/${LOCALE}/signup` },
  { slug: "forgot-password", path: `/${LOCALE}/forgot-password` },
  { slug: "reset-password", path: `/${LOCALE}/reset-password` },
  { slug: "welcome", path: `/${LOCALE}/welcome` },
  { slug: "discover", path: `/${LOCALE}/discover` },
  { slug: "leaderboard", path: `/${LOCALE}/leaderboard` },
  { slug: "events-list", path: `/${LOCALE}/events` },
  { slug: "organizations-list", path: `/${LOCALE}/organizations` },
  { slug: "privacy-policy", path: `/${LOCALE}/privacy-policy` },
  { slug: "invite", path: `/${LOCALE}/invite` },
  { slug: "subscription-success", path: `/${LOCALE}/subscription/success` },
];

const VIEWPORTS = [
  { label: "desktop", width: 1440, height: 900 },
  { label: "mobile", width: 390, height: 844 },
] as const;

async function shoot(page: Page, route: Route, viewport: (typeof VIEWPORTS)[number]) {
  const url = `${BASE_URL}${route.path}`;
  const outFile = path.join(OUT_DIR, `${route.slug}-${viewport.label}.png`);
  const start = Date.now();
  try {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
    const status = resp?.status() ?? 0;
    await page.waitForTimeout(800); // let animations settle
    await page.screenshot({ path: outFile, fullPage: true });
    const ms = Date.now() - start;
    return { route: route.slug, viewport: viewport.label, status, ms, ok: status < 400 };
  } catch (err) {
    return {
      route: route.slug,
      viewport: viewport.label,
      status: 0,
      ms: Date.now() - start,
      ok: false,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const log: Array<Awaited<ReturnType<typeof shoot>>> = [];
  let browser: Browser | null = null;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      deviceScaleFactor: 1,
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 VolauraScreenshotBatch/1.0",
    });
    const page = await context.newPage();

    console.log(`[screenshot] base=${BASE_URL} routes=${PUBLIC_ROUTES.length} viewports=${VIEWPORTS.length}`);
    for (const route of PUBLIC_ROUTES) {
      for (const vp of VIEWPORTS) {
        const result = await shoot(page, route, vp);
        log.push(result);
        const tag = result.ok ? "OK" : "FAIL";
        console.log(
          `  [${tag}] ${result.route}/${result.viewport} status=${result.status} ${result.ms}ms${result.error ? " err=" + result.error : ""}`,
        );
      }
    }
  } finally {
    await browser?.close();
  }

  const manifest = {
    base_url: BASE_URL,
    locale: LOCALE,
    captured_at: new Date().toISOString(),
    total: log.length,
    ok: log.filter((r) => r.ok).length,
    failed: log.filter((r) => !r.ok).length,
    results: log,
  };
  fs.writeFileSync(path.join(OUT_DIR, "_manifest.json"), JSON.stringify(manifest, null, 2), "utf-8");
  console.log(
    `[screenshot] done · ok=${manifest.ok}/${manifest.total} · manifest=${path.relative(process.cwd(), path.join(OUT_DIR, "_manifest.json"))}`,
  );
  if (manifest.failed > 0) process.exitCode = 1;
}

main().catch((e) => {
  console.error("[screenshot] fatal", e);
  process.exit(2);
});
