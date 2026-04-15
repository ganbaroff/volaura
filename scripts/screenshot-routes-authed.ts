/**
 * Auth-gated screenshot batch — P0.3 completion.
 *
 * Flow:
 *   1. POST /api/auth/e2e-setup with X-E2E-Secret → creates confirmed user on prod.
 *   2. Playwright navigates /login, fills email + password, submits.
 *   3. Waits for redirect, screenshots each auth-gated + dynamic route × desktop + mobile.
 *   4. Writes manifest + logs test user_id for later cleanup.
 *
 * Env:
 *   API_URL          default https://volauraapi-production.up.railway.app
 *   WEB_URL          default https://volaura.app
 *   E2E_TEST_SECRET  required (read from apps/api/.env if not set)
 *
 * Usage:
 *   npx tsx scripts/screenshot-routes-authed.ts
 *
 * Cleanup: each run creates one test user in prod auth.users + profiles row.
 * Cleanup is manual via Supabase admin panel or a separate delete script.
 * Track orphan count in memory/atlas/incidents.md#cleanup.
 */
import { chromium, type Browser, type Page } from "playwright";
import * as fs from "node:fs";
import * as path from "node:path";

function readEnvFromFile(envPath: string, key: string): string | undefined {
  try {
    const raw = fs.readFileSync(envPath, "utf-8");
    for (const line of raw.split(/\r?\n/)) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (m && m[1] === key) return m[2].replace(/^["']|["']$/g, "");
    }
  } catch {
    /* ignore */
  }
  return undefined;
}

const API_URL = process.env.API_URL || "https://volauraapi-production.up.railway.app";
const WEB_URL = process.env.WEB_URL || "https://volaura.app";
const LOCALE = "az";
const OUT_DIR = path.resolve(
  __dirname,
  "..",
  "docs/design/ECOSYSTEM-REDESIGN-2026-04-15/screenshots/authed",
);

const E2E_SECRET =
  process.env.E2E_TEST_SECRET ||
  readEnvFromFile(path.resolve(__dirname, "..", "apps/api/.env"), "E2E_TEST_SECRET");

if (!E2E_SECRET) {
  console.error("[screenshot-authed] E2E_TEST_SECRET missing — cannot proceed.");
  process.exit(2);
}

const TIMESTAMP = Date.now();
const TEST_EMAIL = `atlas-screenshot-${TIMESTAMP}@test.volaura.app`;
const TEST_PASSWORD = "AtlasScreenshot1!"; // valid per signup rules: uppercase, digit, symbol, >=8
const TEST_USERNAME = `atlas_shot_${TIMESTAMP}`;

type Route = { slug: string; path: string; authed: boolean; note?: string };

/** Routes that require auth or provide a user-specific view. */
const AUTHED_ROUTES: Route[] = [
  // Personal
  { slug: "onboarding", path: `/${LOCALE}/onboarding`, authed: true },
  { slug: "profile", path: `/${LOCALE}/profile`, authed: true },
  { slug: "profile-edit", path: `/${LOCALE}/profile/edit`, authed: true },
  { slug: "settings", path: `/${LOCALE}/settings`, authed: true },
  { slug: "notifications", path: `/${LOCALE}/notifications`, authed: true },
  // AURA
  { slug: "aura", path: `/${LOCALE}/aura`, authed: true },
  { slug: "aura-contest", path: `/${LOCALE}/aura/contest`, authed: true },
  // Assessment
  { slug: "assessment-list", path: `/${LOCALE}/assessment`, authed: true },
  // Ecosystem surfaces in web
  { slug: "atlas-surface", path: `/${LOCALE}/atlas`, authed: true },
  { slug: "brandedby-surface", path: `/${LOCALE}/brandedby`, authed: true },
  { slug: "life-surface", path: `/${LOCALE}/life`, authed: true },
  { slug: "mindshift-surface", path: `/${LOCALE}/mindshift`, authed: true },
  // Events
  { slug: "event-create", path: `/${LOCALE}/events/create`, authed: true },
  // Org (will show empty-state for new user with no org)
  { slug: "my-organization", path: `/${LOCALE}/my-organization`, authed: true },
  { slug: "my-organization-invite", path: `/${LOCALE}/my-organization/invite`, authed: true },
  { slug: "org-volunteers", path: `/${LOCALE}/org-volunteers`, authed: true },
  // Admin (expected 403 for non-admin — still captures the deny screen)
  { slug: "admin", path: `/${LOCALE}/admin`, authed: true, note: "may 403 for non-admin" },
  { slug: "admin-grievances", path: `/${LOCALE}/admin/grievances`, authed: true, note: "may 403" },
  { slug: "admin-swarm", path: `/${LOCALE}/admin/swarm`, authed: true, note: "may 403" },
  { slug: "admin-users", path: `/${LOCALE}/admin/users`, authed: true, note: "may 403" },
  // Subscription cancel
  { slug: "subscription-cancelled", path: `/${LOCALE}/subscription/cancelled`, authed: true },
];

const VIEWPORTS = [
  { label: "desktop", width: 1440, height: 900 },
  { label: "mobile", width: 390, height: 844 },
] as const;

async function createTestUser(): Promise<{ userId: string; accessToken: string }> {
  const url = `${API_URL}/api/auth/e2e-setup`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-E2E-Secret": E2E_SECRET!,
    },
    body: JSON.stringify({
      email: TEST_EMAIL,
      password: TEST_PASSWORD,
      username: TEST_USERNAME,
      display_name: "Atlas Screenshot",
    }),
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`e2e-setup failed: HTTP ${resp.status} ${body.slice(0, 200)}`);
  }
  const json = (await resp.json()) as { access_token: string; user_id: string };
  return { userId: json.user_id, accessToken: json.access_token };
}

async function loginViaUi(page: Page): Promise<void> {
  await page.goto(`${WEB_URL}/${LOCALE}/login`, { waitUntil: "networkidle", timeout: 30_000 });
  await page.locator("#email").fill(TEST_EMAIL);
  await page.locator("#password").fill(TEST_PASSWORD);
  await Promise.all([
    page.waitForURL((u) => !u.pathname.endsWith("/login"), { timeout: 30_000 }),
    page.locator('button[type="submit"]').click(),
  ]);
}

async function shoot(page: Page, route: Route, viewport: (typeof VIEWPORTS)[number]) {
  const url = `${WEB_URL}${route.path}`;
  const outFile = path.join(OUT_DIR, `${route.slug}-${viewport.label}.png`);
  const start = Date.now();
  try {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
    await page.waitForTimeout(800);
    await page.screenshot({ path: outFile, fullPage: true });
    return {
      route: route.slug,
      viewport: viewport.label,
      status: resp?.status() ?? 0,
      ms: Date.now() - start,
      ok: true,
      note: route.note,
    };
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
  console.log(`[screenshot-authed] api=${API_URL} web=${WEB_URL}`);
  console.log(`[screenshot-authed] creating test user ${TEST_EMAIL} ...`);
  const { userId, accessToken } = await createTestUser();
  console.log(`[screenshot-authed] user_id=${userId} token-len=${accessToken.length}`);

  let browser: Browser | null = null;
  const log: Array<Awaited<ReturnType<typeof shoot>>> = [];
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      deviceScaleFactor: 1,
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 VolauraScreenshotBatch/1.0",
    });
    const page = await context.newPage();

    console.log(`[screenshot-authed] logging in via UI ...`);
    await loginViaUi(page);
    console.log(`[screenshot-authed] logged in, url=${page.url()}`);

    for (const route of AUTHED_ROUTES) {
      for (const vp of VIEWPORTS) {
        const result = await shoot(page, route, vp);
        log.push(result);
        const tag = result.ok ? "OK" : "FAIL";
        console.log(
          `  [${tag}] ${result.route}/${result.viewport} status=${result.status} ${result.ms}ms${result.note ? " note=" + result.note : ""}${result.error ? " err=" + result.error : ""}`,
        );
      }
    }
  } finally {
    await browser?.close();
  }

  const manifest = {
    api_url: API_URL,
    web_url: WEB_URL,
    locale: LOCALE,
    captured_at: new Date().toISOString(),
    test_user: {
      email: TEST_EMAIL,
      username: TEST_USERNAME,
      user_id_for_cleanup: "see console log line above",
      created_at_ts: TIMESTAMP,
    },
    total: log.length,
    ok: log.filter((r) => r.ok).length,
    failed: log.filter((r) => !r.ok).length,
    results: log,
  };
  fs.writeFileSync(path.join(OUT_DIR, "_manifest.json"), JSON.stringify(manifest, null, 2), "utf-8");
  console.log(
    `[screenshot-authed] done · ok=${manifest.ok}/${manifest.total} · manifest=${path.relative(process.cwd(), path.join(OUT_DIR, "_manifest.json"))}`,
  );
  if (manifest.failed > 0) process.exitCode = 1;
}

main().catch((e) => {
  console.error("[screenshot-authed] fatal", e);
  process.exit(2);
});
