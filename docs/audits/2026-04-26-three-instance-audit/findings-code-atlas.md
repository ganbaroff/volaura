# VOLAURA Three-Instance Audit — Code-Atlas Findings
**Instance:** Code-Atlas (Claude Opus 4.6, Claude Code CLI)
**Date:** 2026-04-26
**Time:** ~14:30 Baku
**Scope:** Live tooling — prod health, CI, DNS, daemon, Ollama, GitHub Actions, security, web performance
**Findings:** 26
**P0:** 3 (F-01, F-02, F-05)
**P1:** 8 (F-03, F-04, F-08, F-09, F-12, F-14, F-16, F-26)
**P2:** 9 (F-07, F-10, F-11, F-13, F-17, F-18, F-19, F-20, F-21, F-25)
**P3:** 4 (F-15, F-22, F-23, F-24)

---

### F-01 — Railway backend deployed SHA drifted from HEAD
**Severity:** P0
**Specialist:** Infra
**Surface:** Railway deployment / volauraapi-production.up.railway.app
**Evidence:** `curl /health` returned `git_sha: be2471062b3b`, `git rev-parse --short=12 HEAD` returned `ed07bfbe6327`. 6+ commits behind.
**Impact if unfixed:** Backend serves stale code — any bug fixes, API changes, or security patches from commits after `be247106` are NOT live. Users hit old endpoints. Assessment flow may diverge from frontend expectations.
**Recommended fix:** Push to trigger Railway rebuild: `git push origin main`. If Railway auto-deploy is disabled, trigger manually: `railway up` or dashboard redeploy. Verify post-deploy: `curl -s https://volauraapi-production.up.railway.app/health | jq .git_sha` must match HEAD.
**Sprint slot:** S1 (immediate)
**Estimated effort:** 5 min (AI) + 0 min (CEO)
**Dependencies:** F-02 (CI must pass first for clean deploy)
**Verification step:** `curl -s https://volauraapi-production.up.railway.app/health | jq -r .git_sha` matches `git rev-parse --short=12 origin/main`

---

### F-02 — CI broken 9 consecutive runs — ruff lint errors
**Severity:** P0
**Specialist:** Infra
**Surface:** `.github/workflows/ci.yml` / Backend lint step
**Evidence:** `gh api repos/ganbaroff/volaura/actions/runs` showed 9 consecutive CI failures. `gh run view --log-failed` showed: `atlas_voice.py:8:1 I001 Import block is un-sorted` + `brandedby_refresh_worker.py:32:36 F401 dataclasses.field imported but unused`. Both are auto-fixable ruff errors.
**Impact if unfixed:** CI red blocks Railway auto-deploy (if deploy-on-green is configured), blocks PR merge gates, masks real failures behind lint noise. 9 failures = 9 emails/notifications CEO may be ignoring.
**Recommended fix:** Already fixed in current session: `ruff check --fix` on atlas_voice.py, removed unused `field` import from brandedby_refresh_worker.py. Commit + push resolves.
**Sprint slot:** S1 (immediate — already fixed, needs commit+push)
**Estimated effort:** 5 min (AI — already done)
**Dependencies:** None
**Verification step:** `gh run view --exit-status` on next CI run returns 0

---

### F-03 — /privacy, /terms, /sitemap.xml, /robots.txt all return 404
**Severity:** P1
**Specialist:** Network / Frontend
**Surface:** volaura.app public routes
**Evidence:** `curl -s -L -o /dev/null -w "status=%{http_code}" https://volaura.app/privacy` → 404. Same for /terms (404), /sitemap.xml (404), /robots.txt (404).
**Impact if unfixed:** GDPR compliance risk (/privacy required by law for EU users), Google cannot crawl site (no sitemap/robots.txt), App Store/Play Store review may reject apps linking to missing privacy policy. volaura.app is a production URL used in Stripe Atlas incorporation.
**Recommended fix:** (1) Add `/privacy` and `/terms` pages under `apps/web/src/app/[locale]/(public)/` or as static pages. (2) Add `public/robots.txt` and `public/sitemap.xml` to `apps/web/`. (3) Verify with curl post-deploy.
**Sprint slot:** S1
**Estimated effort:** 2h (AI) + 0.5h review (CEO for legal text)
**Dependencies:** F-05 (force-dynamic removal improves caching of these pages)
**Verification step:** `curl -s -o /dev/null -w "%{http_code}" https://volaura.app/privacy` returns 200

---

### F-04 — volaura.com domain points to someone else's website
**Severity:** P1
**Specialist:** Network / DNS
**Surface:** volaura.com DNS
**Evidence:** `curl -s -I https://volaura.com` returned `HTTP/1.1 301 Moved Permanently`, `Server: LiteSpeed`, `Location: https://www.lauraschreibervoice.com/`. This is NOT Yusif's domain — it belongs to a voice actress.
**Impact if unfixed:** Brand confusion. Anyone typing volaura.com lands on a stranger's website. If volaura.com is available for purchase, it should be acquired. If already owned but misconfigured, DNS needs fixing.
**Recommended fix:** (1) Check domain ownership: `whois volaura.com`. (2) If not owned: evaluate purchase ($8-12 for .com if available, could be parked at higher price). (3) If owned: point DNS A/CNAME to Vercel (76.76.21.21 or cname.vercel-dns.com). (4) Until resolved: ensure all branding/marketing uses volaura.app exclusively.
**Sprint slot:** S2 (CEO decision required)
**Estimated effort:** 30 min (CEO — domain purchase/DNS) + 10 min (AI — Vercel domain config)
**Dependencies:** CEO action
**Verification step:** `curl -s -I https://volaura.com` shows `Server: Vercel` and redirects to volaura.app

---

### F-05 — force-dynamic on root layout kills ALL CDN caching
**Severity:** P0
**Specialist:** Frontend / Infra
**Surface:** `apps/web/src/app/[locale]/layout.tsx:43` + `apps/web/src/app/[locale]/(public)/layout.tsx:1`
**Evidence:** `curl -s -L -I https://volaura.app` showed `Cache-Control: private, no-cache, no-store, max-age=0, must-revalidate` and `X-Vercel-Cache: MISS`. TTFB is 416-878ms for the landing page, which should be ~50ms from Vercel edge cache. Root cause: `export const dynamic = "force-dynamic"` on two layout files opts every route out of static generation.
**Impact if unfixed:** Every page load for every visitor SSR-renders on Vercel serverless, no CDN edge caching. Landing page TTFB 10-20x worse than it could be. Vercel billing scales with requests instead of being cached. Core Web Vitals FCP/LCP significantly degraded.
**Recommended fix:** Remove `export const dynamic = "force-dynamic"` from both layout files. The locale layout only calls `initTranslations(locale, ["common"])` which reads local JSON — no dynamic data. Individual pages that truly need SSR (dashboard, profile) should declare their own `dynamic = "force-dynamic"`.
**Sprint slot:** S1
**Estimated effort:** 15 min (AI)
**Dependencies:** None
**Verification step:** `curl -s -L -I https://volaura.app | grep -i "x-vercel-cache"` shows `HIT` or `STALE` instead of `MISS`

---

### F-06 — code-index.json is empty (0 modules, 0 endpoints)
**Severity:** P1
**Specialist:** Daemon / Swarm
**Surface:** `memory/swarm/code-index.json`
**Evidence:** `python -c "import json; d=json.load(open('memory/swarm/code-index.json')); print(len(d.get('modules',{})), len(d.get('endpoints',[])))"` → `0 0`. The `built_at` says `2026-04-26T09:49` but content is empty. Swarm agents referencing this index operate on zero data.
**Impact if unfixed:** All swarm perspectives that read code-index get empty context. Whistleblower flags from 3 separate runs flagged "agents simulating on stale index" — this is the root cause. Swarm decisions are baseless.
**Recommended fix:** (1) Investigate why the index builder wrote empty data — check the builder script for errors. (2) Regenerate: `python -m packages.swarm.build_code_index` or equivalent. (3) Add a CI workflow step that validates `modules > 0 && endpoints > 0` post-build.
**Sprint slot:** S1
**Estimated effort:** 1h (AI)
**Dependencies:** None
**Verification step:** `python -c "import json; d=json.load(open('memory/swarm/code-index.json')); print(len(d.get('modules',{})))"` returns >10

---

### F-07 — Constitution file header says v1.2, content includes v1.7
**Severity:** P2
**Specialist:** Governance
**Surface:** `docs/ECOSYSTEM-CONSTITUTION.md` line 1
**Evidence:** `head -1 docs/ECOSYSTEM-CONSTITUTION.md` → `# ECOSYSTEM CONSTITUTION v1.2`. But revision history at line 1124 documents v1.7 changes. `CLAUDE.md:3` references `v1.7 — supreme law`. The file was never re-headed after revisions were appended.
**Impact if unfixed:** Confusion between instances about which version is canonical. Browser-Atlas and Codex may reference different versions. Any automated version-checking breaks.
**Recommended fix:** Edit line 1: `# ECOSYSTEM CONSTITUTION v1.7`. Also update line 6 to reflect the latest audit. Commit with message "fix: Constitution header v1.2 → v1.7 (content already at v1.7)".
**Sprint slot:** S2
**Estimated effort:** 5 min (AI)
**Dependencies:** None
**Verification step:** `head -1 docs/ECOSYSTEM-CONSTITUTION.md` contains `v1.7`

---

### F-08 — Daemon provider failure rate 40% (8 of 20 events)
**Severity:** P1
**Specialist:** Daemon / LLM
**Surface:** `memory/atlas/work-queue/daemon.log.jsonl`
**Evidence:** Log analysis: 20 total events, 8 `provider_failed`, 5 `task_start`, 5 `task_done`, 2 `daemon_start`. 40% of all events are provider failures.
**Impact if unfixed:** Swarm tasks succeed only after multiple retries, burning time and credits. If all providers fail simultaneously, daemon halts silently with no alerting.
**Recommended fix:** (1) Analyze which providers fail — add provider name to error logs. (2) Test Ollama local (qwen3:8b) as primary to reduce external API dependency. (3) Add daemon health metric to error_watcher.py (provider_failure_rate_1h).
**Sprint slot:** S3
**Estimated effort:** 2h (AI)
**Dependencies:** F-10 (Ollama latency evaluation)
**Verification step:** Next 20 daemon events show <20% provider_failed rate

---

### F-09 — atlas-watchdog and obligation-nag haven't run in 7 days
**Severity:** P1
**Specialist:** Cron / GitHub Actions
**Surface:** `.github/workflows/atlas-watchdog.yml`, `atlas-obligation-nag.yml`
**Evidence:** `gh api .../atlas-watchdog.yml/runs?per_page=1` → last run `2026-04-19T15:07:26Z` (7 days ago). Same for obligation-nag: `2026-04-19T13:42:31Z`. Both are scheduled crons that should fire daily.
**Impact if unfixed:** Watchdog cannot detect workflow failures or drift. Obligation nag cannot alert on approaching deadlines. Silent failure — nobody knows these are dead.
**Recommended fix:** (1) Check workflow cron syntax — `schedule:` may have wrong cron expression. (2) GitHub Actions disables crons after 60 days of no repo activity on that workflow's trigger branch — push a no-op commit or manually trigger: `gh workflow run atlas-watchdog.yml`. (3) Verify next day.
**Sprint slot:** S1
**Estimated effort:** 30 min (AI)
**Dependencies:** None
**Verification step:** `gh api .../atlas-watchdog.yml/runs?per_page=1 --jq '.workflow_runs[0].created_at'` shows today's date

---

### F-10 — Ollama qwen3:8b latency 22.5 seconds for trivial prompt
**Severity:** P2
**Specialist:** Infra / LLM
**Surface:** Ollama localhost:11434 / RTX 5060 GPU
**Evidence:** `curl -X POST localhost:11434/api/generate -d '{"model":"qwen3:8b","prompt":"Say hello in 5 words","stream":false}'` → response in 22494ms. `nvidia-smi` showed only 4% GPU utilization and 1652/8151 MiB VRAM used. Model may not be loaded into GPU memory or GPU offloading is partial.
**Impact if unfixed:** Local LLM is unusable for real-time tasks. Daemon falls back to external APIs (causing the 40% provider failures in F-08). GPU is bought but idle.
**Recommended fix:** (1) Check Ollama GPU offloading: `OLLAMA_NUM_GPU=999` to force full GPU load. (2) Verify CUDA: `ollama ps` should show qwen3:8b with GPU layers. (3) Pre-load model: `curl localhost:11434/api/generate -d '{"model":"qwen3:8b","keep_alive":"24h"}'`. (4) If still slow, try smaller model (gemma3:4b at 3.3GB should fit fully in VRAM).
**Sprint slot:** S3
**Estimated effort:** 1h (AI)
**Dependencies:** None
**Verification step:** Same trivial prompt returns in <5000ms

---

### F-11 — 36 unresolved whistleblower flags across 5 daemon runs
**Severity:** P2
**Specialist:** Governance / Swarm
**Surface:** `memory/atlas/work-queue/done/*/result.json`
**Evidence:** Aggregation of all result.json files found 36 whistleblower_flags. Recurring themes: (1) Courier-loop security — unverified AI-to-AI state transfer, zip execution with full .env access (raised by 7 perspectives across 2 runs). (2) Stale code-index — agents operating on empty index (raised by 4 perspectives across 3 runs). (3) Law 2 (Energy Adaptation) unenforced across 4/5 products (raised by 2 perspectives).
**Impact if unfixed:** Whistleblower flags are the swarm's self-correction mechanism. Ignoring recurring flags means the swarm raises alarms nobody reads. Constitutional violations accumulate.
**Recommended fix:** (1) Create a whistleblower triage workflow that reads all open flags, deduplicates by theme, and creates atlas_obligations rows. (2) Close flags that are addressed by other findings (F-06 closes stale-index flags). (3) For courier-loop security: see F-14 synthesis.
**Sprint slot:** S4
**Estimated effort:** 3h (AI)
**Dependencies:** F-06, F-14
**Verification step:** Next daemon run produces 0 repeat flags on closed themes

---

### F-12 — Vercel Cache-Control headers prevent all caching
**Severity:** P1
**Specialist:** Frontend / Infra
**Surface:** Vercel deployment / volaura.app response headers
**Evidence:** `curl -s -L -I https://volaura.app` returned `Cache-Control: private, no-cache, no-store, max-age=0, must-revalidate`. This is set by Next.js because of `force-dynamic` (see F-05). Additionally, `next.config.mjs` only defines security headers (`X-Frame-Options`, etc.) — no explicit `Cache-Control` for `/_next/static/` or image assets.
**Impact if unfixed:** Every static JS/CSS chunk, every font file, every icon is served without long-term caching directives at the application level. While Vercel sets immutable headers on `_next/static` by default, custom assets in `/icons/` and `/images/` don't benefit.
**Recommended fix:** (1) Fix F-05 first (removes force-dynamic). (2) Add explicit cache headers in `next.config.mjs` headers() for `/_next/static/(.*)` (immutable, 1 year) and `/icons/(.*)` (30 days).
**Sprint slot:** S1 (coupled with F-05)
**Estimated effort:** 15 min (AI)
**Dependencies:** F-05
**Verification step:** `curl -s -I "https://volaura.app/_next/static/chunks/main-*.js" | grep cache-control` shows `immutable`

---

### F-13 — rls-tests workflow failing
**Severity:** P2
**Specialist:** DB / CI
**Surface:** `.github/workflows/rls-tests.yml`
**Evidence:** `gh api .../rls-tests.yml/runs?per_page=1` → `failure | 2026-04-25T16:48:37Z`. Log showed Node.js 20 deprecation warnings from `actions/checkout@v4` and `supabase/setup-cli@v1`. Actual pgTAP test output not visible in failed log tail — failure may be in setup, not tests.
**Impact if unfixed:** RLS policies are not continuously verified. A regression in row-level security could go undetected, exposing user data across tenant boundaries.
**Recommended fix:** (1) Read full failure log to determine if issue is Node.js deprecation or actual pgTAP failure. (2) If Node.js: add `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` env var to workflow. (3) If pgTAP: fix the failing test or the migration it tests against.
**Sprint slot:** S2
**Estimated effort:** 1h (AI)
**Dependencies:** None
**Verification step:** `gh workflow run rls-tests.yml` + `gh run list --workflow=rls-tests.yml --limit=1` shows success

---

### F-14 — Courier loop design lacks signing protocol (P0 vote result)
**Severity:** P1
**Specialist:** Security-runtime / Cross-instance
**Surface:** `memory/atlas/work-queue/done/2026-04-26-courier-loop-design/`
**Evidence:** Daemon swarm voted 13/13 on courier-loop design. 7 perspectives raised P0 whistleblower flags about "unverified AI-to-AI state transfer enables irreversible constitutional violation". The result.json exists but no synthesis doc at `docs/architecture/cross-instance-courier-signing-protocol.md` was created yet.
**Impact if unfixed:** Cross-instance communication (Code-Atlas ↔ Browser-Atlas ↔ Codex) via CEO-couriered zips has no integrity verification. A corrupted or tampered zip could inject false state into any Atlas instance.
**Recommended fix:** (1) Synthesize the 13 perspective outputs into a concrete protocol doc. (2) Minimum viable: SHA-256 hash of zip contents verified before extraction. (3) Medium-term: Ed25519 signing per instance with public keys in `memory/atlas/keys/`.
**Sprint slot:** S3
**Estimated effort:** 4h (AI)
**Dependencies:** None
**Verification step:** `docs/architecture/cross-instance-courier-signing-protocol.md` exists with concrete implementation steps

---

### F-15 — DEBT-001 (230 AZN) still open, no revenue landed
**Severity:** P3
**Specialist:** Finance
**Surface:** `memory/atlas/atlas-debts-to-ceo.md`
**Evidence:** File content: `Open balance: 230 AZN (~$135 USD) — credited-pending against Atlas dev revenue share`. Status: `credited-pending`. Closure trigger: first revenue line ≥ 230 AZN. No Stripe or Mercury revenue detected.
**Impact if unfixed:** Debt accumulates visibility fatigue — CEO sees "open" every session. No action needed from AI, but the ledger must stay visible until revenue offsets it.
**Recommended fix:** No fix — this is a tracking item. Ensure proactive-scan gate surfaces this in every CEO-facing status. When first revenue lands, auto-close with tx-id.
**Sprint slot:** N/A (tracking)
**Estimated effort:** 0
**Dependencies:** Revenue
**Verification step:** `grep "status:" memory/atlas/atlas-debts-to-ceo.md` shows `credited-pending` or `closed-credited`

---

### F-16 — SW-purge script in head runs on every page load despite PWA disabled
**Severity:** P1
**Specialist:** Frontend
**Surface:** `apps/web/src/app/[locale]/layout.tsx:62-71`
**Evidence:** Codebase audit (Agent/Explore) found `<script dangerouslySetInnerHTML>` in `<head>` that calls `navigator.serviceWorker.getRegistrations()` and `caches.keys()` on every page load. `next.config.mjs:51-54` shows `@ducanh2912/next-pwa` with `disable: true`.
**Impact if unfixed:** Synchronous script in `<head>` delays First Contentful Paint. Two async API calls (SW registration scan + cache key scan) execute on every load for every visitor, finding nothing (PWA is disabled). Wasted CPU time on mobile devices.
**Recommended fix:** Remove the entire `<script dangerouslySetInnerHTML>` block from the locale layout. The PWA is disabled — there's nothing to purge. Also remove `@ducanh2912/next-pwa` from devDependencies and the `withPWA` wrapper from next.config.mjs.
**Sprint slot:** S1
**Estimated effort:** 15 min (AI)
**Dependencies:** None
**Verification step:** `grep -r "dangerouslySetInnerHTML" apps/web/src/app/` returns no SW-purge script

---

### F-17 — All 8 landing components are "use client"
**Severity:** P2
**Specialist:** Frontend
**Surface:** `apps/web/src/components/landing/*.tsx`
**Evidence:** Codebase audit found all 8 landing components (hero-section, features-grid, how-it-works, org-cta, sample-aura-preview, landing-nav, landing-footer, social-proof) use `"use client"`. LandingNav, LandingFooter, and SocialProof have no interactive state — they use `useTranslation()` which forces client, but translated strings could be passed as props from server.
**Impact if unfixed:** Entire landing page ships as client-side bundle. Framer Motion (~100KB) and all component code must be downloaded, parsed, and hydrated before the page is interactive. Server Components would stream HTML immediately.
**Recommended fix:** (1) Convert LandingNav, LandingFooter to Server Components by passing `t()` results as props. (2) For animation components: use thin client wrappers with server-rendered content shells. (3) SocialProof: fetch stats server-side in page.tsx, pass as props.
**Sprint slot:** S4
**Estimated effort:** 4h (AI)
**Dependencies:** F-05 (static rendering must work first)
**Verification step:** `grep -l '"use client"' apps/web/src/components/landing/*.tsx | wc -l` drops from 8 to ≤4

---

### F-18 — Duplicate API fetch: social-proof.tsx raw fetch duplicates TanStack Query
**Severity:** P2
**Specialist:** Frontend
**Surface:** `apps/web/src/components/landing/social-proof.tsx:11-15`
**Evidence:** Codebase audit found `SocialProof` makes raw `fetch("/api/stats/public")` in useEffect — same endpoint already fetched by `ImpactTicker` via `usePublicStats()` TanStack Query hook. Two network requests to same endpoint on every landing page load.
**Impact if unfixed:** Double network request on landing page, no caching, no loading state. Wastes bandwidth and shows stale 0-values during fetch.
**Recommended fix:** Replace raw fetch with `usePublicStats()` hook from `@/hooks/queries/use-public-stats`.
**Sprint slot:** S2
**Estimated effort:** 15 min (AI)
**Dependencies:** None
**Verification step:** Network tab shows single request to `/api/stats/public` on landing page load

---

### F-19 — Raw img tags without width/height cause CLS
**Severity:** P2
**Specialist:** Frontend
**Surface:** `apps/web/src/components/ui/avatar.tsx:80`, `tribe-card.tsx:210`, `organizations/page.tsx:44`
**Evidence:** Codebase audit found 3 locations using native `<img>` tags without `width`/`height` attributes and ESLint suppression comments. No layout dimensions means browser cannot reserve space before image loads.
**Impact if unfixed:** Cumulative Layout Shift (CLS) — a Core Web Vitals metric. Visible content jumps when images load. Hurts Google search ranking.
**Recommended fix:** Add explicit width/height to all `<img>` tags, or switch to `next/image` with `unoptimized` prop for external OAuth CDN URLs.
**Sprint slot:** S3
**Estimated effort:** 30 min (AI)
**Dependencies:** None
**Verification step:** `grep -rn '<img' apps/web/src/ | grep -v 'width'` returns empty

---

### F-20 — Recharts (~300KB) imported statically, no code splitting
**Severity:** P2
**Specialist:** Frontend / Bundle
**Surface:** `apps/web/src/components/aura/radar-chart.tsx:1-13`
**Evidence:** Codebase audit found Recharts imported at component level without `next/dynamic`. While `optimizePackageImports: ["recharts"]` helps tree-shaking, there's no dynamic import wrapper.
**Impact if unfixed:** Recharts (~300KB) included in page bundle for any route that imports AuraRadarChart, even before user scrolls to the chart.
**Recommended fix:** Wrap with `next/dynamic(() => import("@/components/aura/radar-chart"), { ssr: false })` at usage sites.
**Sprint slot:** S4
**Estimated effort:** 15 min (AI)
**Dependencies:** None
**Verification step:** Recharts chunk loads only when chart component is visible (Network tab)

---

### F-21 — Google Fonts: no display strategy, unnecessary latin-ext subset
**Severity:** P2
**Specialist:** Frontend
**Surface:** `apps/web/src/app/[locale]/layout.tsx:11-16`
**Evidence:** Codebase audit: `Inter` loaded with `subsets: ["latin", "latin-ext"]` — latin-ext doubles font payload for AZ/EN visitors who only need basic Latin. `Plus_Jakarta_Sans` has no `display` option set (defaults to `swap` causing FOUT for headlines).
**Impact if unfixed:** Unnecessary font bytes downloaded. FOUT on headline text.
**Recommended fix:** (1) Remove `latin-ext` from Inter (AZ uses basic Latin). (2) Add `display: "optional"` to Plus_Jakarta_Sans (headline font — system font fallback is acceptable). (3) Remove unused weight 400 from Plus_Jakarta_Sans if confirmed unused.
**Sprint slot:** S3
**Estimated effort:** 15 min (AI)
**Dependencies:** None
**Verification step:** Browser DevTools Network shows smaller font payload

---

### F-22 — Middleware runs Supabase session refresh on unauthenticated public pages
**Severity:** P3
**Specialist:** Frontend / Auth
**Surface:** `apps/web/src/middleware.ts`
**Evidence:** Codebase audit: `updateSession` calls `supabase.auth.getUser()` on every non-static request including landing page for unauthenticated visitors. Adds ~10-50ms server latency per request.
**Recommended fix:** Check pathname against known public routes (landing, events, organizations, verify) before calling `updateSession`. Skip for those paths.
**Sprint slot:** S5
**Estimated effort:** 30 min (AI)
**Dependencies:** None
**Verification step:** Landing page TTFB drops by 10-50ms after middleware optimization

---

### F-23 — ANUS project: massive, disorganized, no integration path
**Severity:** P3
**Specialist:** Cross-instance
**Surface:** `C:\Users\user\OneDrive\Documents\GitHub\ANUS`
**Evidence:** `ls` found 200+ files: 80+ zeus_*.py scripts, 50+ *_REPORT.md files, `.zeus/` folder with config/logs/monitoring. Entry points include `zeus.py`, `launch_zeus.py`, `zeus_autonomous_computer_control.py`, `zeus_ecosystem_orchestrator.py`. Heavy Python with Flask API, Telegram bot, browser automation, social media integration. No CLAUDE.md, no clear entry point, no tests passing.
**Impact if unfixed:** ANUS (Autonomous Neural Unified System) is the proto-Atlas — Yusif's earlier attempt at an autonomous AI controller. It contains valuable patterns (Telegram bot control, window management, social automation) buried under 200+ files of iteration. Without integration roadmap, these patterns stay siloed.
**Recommended fix:** Separate finding — write `docs/architecture/anus-atlas-integration-roadmap.md` with: (1) Inventory of salvageable modules. (2) Map ANUS patterns → VOLAURA equivalents. (3) Migration priority. This is a research task, not urgent.
**Sprint slot:** S8
**Estimated effort:** 4h research (AI)
**Dependencies:** None
**Verification step:** Roadmap file exists with module inventory

---

### F-24 — for-ceo/index.html links not greppable (JS-rendered cards)
**Severity:** P3
**Specialist:** Frontend / CEO-UX
**Surface:** `for-ceo/index.html`
**Evidence:** `grep -oP 'href="[^"]*"' for-ceo/index.html` returned empty. The HTML uses inline JS cards with no standard `<a href>` links — content is rendered via JavaScript template literals.
**Impact if unfixed:** Links not crawlable, not usable with JavaScript disabled, not verifiable by grep-based automated checks. CEO's index page depends on JS execution.
**Recommended fix:** Add standard `<a href="...">` links to card elements. JS enhancement on top is fine, but base links must work without JS.
**Sprint slot:** S5
**Estimated effort:** 1h (AI)
**Dependencies:** None
**Verification step:** `grep -oP 'href="[^"]*"' for-ceo/index.html | wc -l` returns >5

---

### F-25 — AtlasSwarmDaemon Scheduled Task: no LastRunTime, no NextRunTime
**Severity:** P2
**Specialist:** Daemon / Windows
**Surface:** Windows Scheduled Task `AtlasSwarmDaemon`
**Evidence:** PowerShell `Get-ScheduledTask -TaskName 'AtlasSwarmDaemon'` returned `State: Ready` but `LastRunTime`, `NextRunTime`, `LastTaskResult` all blank. Task registered but never ran via the scheduler — daemon was started manually or via daemon.log shows only 2 starts.
**Impact if unfixed:** Daemon does not auto-start on login/reboot. If Yusif restarts the machine, daemon stays dead until manually started.
**Recommended fix:** (1) Check task trigger — is it AtLogOn? (2) Test: `schtasks /Run /TN "AtlasSwarmDaemon"` manually. (3) Verify the action command path is correct (absolute path to Python + daemon script). (4) Add a trigger for machine unlock (not just logon).
**Sprint slot:** S3
**Estimated effort:** 1h (AI + CEO testing)
**Dependencies:** None
**Verification step:** `Get-ScheduledTask -TaskName 'AtlasSwarmDaemon' | Select LastRunTime` shows recent timestamp

---

### F-26 — Web performance: TTFB 416-878ms on landing page
**Severity:** P1
**Specialist:** Frontend / Infra
**Surface:** volaura.app landing page
**Evidence:** `curl -s -L -o /dev/null -w "ttfb=%{time_starttransfer}s" https://volaura.app` → 416ms (best), 878ms (worst across tests). For comparison, a Vercel-cached static page typically returns in 30-60ms from fra1 edge.
**Impact if unfixed:** Every first-time visitor waits ~500ms+ before seeing any content. Mobile users on 3G/4G add network latency on top. Google PageSpeed Insights will flag this, hurting SEO ranking.
**Recommended fix:** Fixing F-05 (remove force-dynamic) is the primary fix. Additionally: F-16 (remove SW-purge script), F-21 (font optimization), F-17 (server components for landing). Combined effect should bring TTFB to <100ms.
**Sprint slot:** S1 (via F-05)
**Estimated effort:** Covered by F-05
**Dependencies:** F-05, F-16, F-17, F-21
**Verification step:** `curl -s -L -o /dev/null -w "%{time_starttransfer}" https://volaura.app` < 0.15s
