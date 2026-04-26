## apps/tg-mini

### F-01 — tg-mini hardcodes the deprecated backend host
**Severity:** P1
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\tg-mini\src\api.ts:1-2`
**Evidence:** 
```ts
1: // API client for VOLAURA backend (Railway)
2: const API_BASE = import.meta.env.VITE_API_URL || 'https://volauraapi-production.up.railway.app/api'
```
**Impact if unfixed:** The mini app points to the retired `volauraapi-production` origin instead of the current Railway backend. In any environment without an explicit `VITE_API_URL`, every fetch silently targets a dead host and the Telegram surface degrades into empty-state fallbacks instead of showing real swarm state.
**Recommended fix:** 
```ts
// apps/tg-mini/src/api.ts
const API_BASE =
  import.meta.env.VITE_API_URL ||
  "https://modest-happiness-production.up.railway.app/api";
```
**Sprint slot:** S1
**Estimated effort:** 0.25h
**Dependencies:** none
**Test added:** no

### F-02 — tg-mini never unwraps the admin API envelope, so lists stay empty even when the API succeeds
**Severity:** P1
**Specialist:** Type Safety
**Surface:** `C:\Projects\VOLAURA\apps\tg-mini\src\api.ts:32-47`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:589-595`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:636-641`
**Evidence:** 
```ts
32: export async function fetchProposals(): Promise<SwarmDigest> {
34:   const res = await fetch(`${API_BASE}/swarm/proposals`)
36:   return await res.json()
42: export async function fetchAgents(): Promise<SwarmAgent[]> {
46:   const data = await res.json()
47:   return data.agents || []
```
```py
589:         return {
590:             "data": {
591:                 "agents": agents,
592:                 "total_tracked": len(agents),
593:                 "total_untracked": data.get("_uninitialized_count", 0),
594:             }
595:         }
636:         return {"data": {"proposals": proposals, "summary": summary}}
```
**Impact if unfixed:** `fetchAgents()` looks for `data.agents` at the top level even though the API returns `{data:{agents:[...]}}`, and `fetchProposals()` hands raw `{data:{proposals,...}}` to callers that expect `{proposals:[...]}`. The result is a false-green UI: the app renders, but always shows zero agents and zero proposals unless a future caller manually compensates.
**Recommended fix:** 
```ts
// apps/tg-mini/src/api.ts
type AgentsResponse = { data: { agents: SwarmAgent[] } };
type ProposalsResponse = { data: { proposals: Proposal[]; summary: { pending: number; approved: number; rejected: number } } };

export async function fetchProposals(): Promise<SwarmDigest> {
  try {
    const res = await fetch(`${API_BASE}/swarm/proposals`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = (await res.json()) as ProposalsResponse;
    return {
      proposals: json.data.proposals ?? [],
      total: json.data.summary.pending ?? 0,
    };
  } catch {
    return { proposals: [], total: 0 };
  }
}

export async function fetchAgents(): Promise<SwarmAgent[]> {
  try {
    const res = await fetch(`${API_BASE}/swarm/agents`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = (await res.json()) as AgentsResponse;
    return json.data.agents ?? [];
  } catch {
    return [];
  }
}
```
**Sprint slot:** S1
**Estimated effort:** 0.75h
**Dependencies:** F-01
**Test added:** yes

### F-03 — tg-mini proposal action client hits a route that does not exist and sends unsupported action values
**Severity:** P1
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\tg-mini\src\api.ts:53-56`; `C:\Projects\VOLAURA\apps\tg-mini\src\pages\ProposalsPage.tsx:28-35`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:644-660`
**Evidence:** 
```ts
53: export async function actOnProposal(id: string, action: 'act' | 'dismiss' | 'defer' | 'execute'): Promise<boolean> {
55:   const res = await fetch(`${API_BASE}/swarm/proposals/${id}/${action}`, { method: 'POST' })
```
```ts
28:   const handleAction = async (id: string, action: 'act' | 'dismiss' | 'execute') => {
30:     const ok = await actOnProposal(id, action)
```
```py
644: @router.post("/swarm/proposals/{proposal_id}/decide")
655:     body = await request.json()
656:     action = body.get("action", "")  # "approve" | "dismiss" | "defer"
657:     if action not in ("approve", "dismiss", "defer"):
```
**Impact if unfixed:** Telegram users cannot act on proposals even if authentication is fixed. The client posts to `/swarm/proposals/{id}/{action}` while the backend only accepts `/swarm/proposals/{id}/decide` with JSON `{action:"approve"|"dismiss"|"defer"}`. Two UI buttons (`act`, `execute`) map to no backend action at all, so every approval flow is guaranteed to 404 or 400.
**Recommended fix:** 
```ts
// apps/tg-mini/src/api.ts
export async function actOnProposal(
  id: string,
  action: "approve" | "dismiss" | "defer",
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/swarm/proposals/${id}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
```
```ts
// apps/tg-mini/src/pages/ProposalsPage.tsx
const handleAction = async (id: string, action: "approve" | "dismiss" | "defer") => {
  ...
}
...
onClick={() => handleAction(p.id, "approve")}
onClick={() => handleAction(p.id, "defer")}
onClick={() => handleAction(p.id, "dismiss")}
```
**Sprint slot:** S1
**Estimated effort:** 1h
**Dependencies:** F-02
**Test added:** yes

### F-04 — tg-mini calls admin-only swarm endpoints without any authentication material
**Severity:** P1
**Specialist:** Security
**Surface:** `C:\Projects\VOLAURA\apps\tg-mini\src\api.ts:34-35`; `C:\Projects\VOLAURA\apps\tg-mini\src\api.ts:44-46`; `C:\Projects\VOLAURA\apps\tg-mini\src\api.ts:55-56`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:557-560`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:605-609`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:646-649`
**Evidence:** 
```ts
34:     const res = await fetch(`${API_BASE}/swarm/proposals`)
44:     const res = await fetch(`${API_BASE}/swarm/agents`)
55:     const res = await fetch(`${API_BASE}/swarm/proposals/${id}/${action}`, { method: 'POST' })
```
```py
557: async def get_swarm_agents(
558:     request: Request,
559:     admin_id: PlatformAdminId,
560: ) -> dict:
605: async def get_swarm_proposals(
606:     request: Request,
607:     admin_id: PlatformAdminId,
608:     status_filter: str | None = Query(None, alias="status"),
646: async def decide_proposal(
647:     request: Request,
648:     proposal_id: str,
649:     admin_id: PlatformAdminId,
```
**Impact if unfixed:** Even after the host and route bugs are fixed, the Telegram mini app still cannot operate because every swarm endpoint requires an authenticated platform admin context and the client never sends an `Authorization` header or Telegram-init-data-derived session. This makes the entire surface a dead shell in production.
**Recommended fix:** 
```ts
// apps/tg-mini/src/api.ts
function authHeaders(): HeadersInit {
  const token = sessionStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const res = await fetch(`${API_BASE}/swarm/proposals`, { headers: authHeaders() });
const res = await fetch(`${API_BASE}/swarm/agents`, { headers: authHeaders() });
const res = await fetch(`${API_BASE}/swarm/proposals/${id}/decide`, {
  method: "POST",
  headers: { "Content-Type": "application/json", ...authHeaders() },
  body: JSON.stringify({ action }),
});
```
**Sprint slot:** S1
**Estimated effort:** 2h
**Dependencies:** F-01, F-03
**Test added:** yes

### F-05 — tg-mini is outside the CI pipeline and has no test script, so its contract drift ships undetected
**Severity:** P1
**Specialist:** Test
**Surface:** `C:\Projects\VOLAURA\.github\workflows\ci.yml:11-18`; `C:\Projects\VOLAURA\.github\workflows\ci.yml:38-42`; `C:\Projects\VOLAURA\.github\workflows\ci.yml:44-50`; `C:\Projects\VOLAURA\apps\tg-mini\package.json:6-10`
**Evidence:** 
```yaml
11:   frontend:
15:     defaults:
16:       run:
17:         working-directory: apps/web
38:       - name: Tests
39:         run: pnpm vitest run
41:       - name: Build
42:         run: pnpm build
44:   backend:
48:     defaults:
49:       run:
50:         working-directory: apps/api
```
```json
6:   "scripts": {
7:     "dev": "vite",
8:     "build": "tsc -b && vite build",
9:     "preview": "vite preview"
10:   },
```
**Impact if unfixed:** The Telegram mini app can regress indefinitely without tripping any gate: CI only enters `apps/web` and `apps/api`, and `apps/tg-mini` has neither a `test` script nor any discovered `*.test.ts(x)` files. That is why the broken host, wrong route shape, and missing auth all made it to `main` together.
**Recommended fix:** 
```yaml
# .github/workflows/ci.yml
  tg-mini:
    name: Telegram Mini App
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/tg-mini
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
      - run: npm run test
```
```json
// apps/tg-mini/package.json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "preview": "vite preview",
  "test": "vitest run"
}
```
**Sprint slot:** S1
**Estimated effort:** 1.5h
**Dependencies:** none
**Test added:** yes

### F-06 — tg-mini is not a shippable 3D app; it is a thin 2D shell with three pages and no rendering stack
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\tg-mini\package.json:11-24`; `C:\Projects\VOLAURA\apps\tg-mini\src\App.tsx:20-24`
**Evidence:** 
```json
11:   "dependencies": {
12:     "@telegram-apps/telegram-ui": "^2.1.9",
13:     "@telegram-apps/sdk-react": "^3.0.0",
14:     "react": "^18.3.1",
15:     "react-dom": "^18.3.1",
16:     "react-router-dom": "^6.30.1"
17:   },
```
```tsx
20:           <Routes>
21:             <Route path="/" element={<HomePage />} />
22:             <Route path="/proposals" element={<ProposalsPage />} />
23:             <Route path="/agents" element={<AgentsPage />} />
24:           </Routes>
```
**Impact if unfixed:** The repository claims a 3D Telegram surface, but the committed implementation has no 3D renderer, scene graph, canvas/WebGL library, asset pipeline, or interaction layer. Executors who treat this as a nearly-finished 3D client will waste time debugging the wrong class of problem instead of acknowledging it is currently a minimal dashboard prototype.
**Recommended fix:** 
```md
1. Reclassify apps/tg-mini as "admin shell prototype" in docs until a 3D stack lands.
2. If 3D is required, add the chosen stack explicitly:
   - dependency: @react-three/fiber + three
   - route: /scene
   - source tree: src/scene/*
3. Add one smoke test that asserts the intended route exists before calling it "3D-ready".
```
**Sprint slot:** S6
**Estimated effort:** 6h
**Dependencies:** product decision
**Test added:** no

## backend / security / RLS

### F-07 — admin swarm endpoints resolve `memory/swarm` from `apps/` instead of repo root and silently return empty 200s
**Severity:** P1
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:565-568`; `C:\Projects\VOLAURA\apps\api\app\routers\admin.py:614-617`
**Evidence:** 
```py
565:     state_path = Path(__file__).parent.parent.parent.parent / "memory" / "swarm" / "agent-state.json"
566:     try:
567:         with open(state_path, encoding="utf-8") as f:
568:             data = _json.load(f)
```
```py
614:     proposals_path = Path(__file__).parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"
615:     try:
616:         with open(proposals_path, encoding="utf-8") as f:
617:             data = _json.load(f)
```
**Impact if unfixed:** `admin.py` lives at `apps/api/app/routers/admin.py`, so four `.parent` hops land on `C:\Projects\VOLAURA\apps`, not `C:\Projects\VOLAURA`. The code therefore looks for `C:\Projects\VOLAURA\apps\memory\swarm\*.json`, which does not exist, triggers the `FileNotFoundError` branch, and returns empty success responses. The AI Office surface can appear healthy while reading zero real swarm state.
**Recommended fix:** 
```py
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SWARM_MEMORY_DIR = REPO_ROOT / "memory" / "swarm"

state_path = SWARM_MEMORY_DIR / "agent-state.json"
proposals_path = SWARM_MEMORY_DIR / "proposals.json"
```
**Sprint slot:** S1
**Estimated effort:** 0.5h
**Dependencies:** none
**Test added:** yes

### F-08 — admin swarm endpoint tests mock `open()` so aggressively that they miss the broken filesystem root
**Severity:** P2
**Specialist:** Test
**Surface:** `C:\Projects\VOLAURA\apps\api\tests\test_admin_endpoints.py:641-672`; `C:\Projects\VOLAURA\apps\api\tests\test_admin_endpoints.py:683-700`; `C:\Projects\VOLAURA\apps\api\tests\test_admin_endpoints.py:730-762`
**Evidence:** 
```py
641:     async def test_agents_returns_list_from_file(self):
669:                 patch("json.load", return_value=agent_state),
672:                     resp = await client.get("/api/admin/swarm/agents")
```
```py
683:     async def test_agents_file_not_found_returns_empty(self):
684:             with patch("builtins.open", side_effect=FileNotFoundError("no file")):
686:                     resp = await client.get("/api/admin/swarm/agents")
```
```py
730:     async def test_proposals_returns_list(self):
733:             with patch("builtins.open", side_effect=FileNotFoundError()):
735:                     resp = await client.get("/api/admin/swarm/proposals")
```
**Impact if unfixed:** The suite proves only that mocked file IO produces the expected JSON shape. It never asserts that `admin.py` resolves the correct repo-root path, so the production bug in F-07 survives green tests. This is exactly the kind of mock/prod divergence the repo’s own testing doctrine says to avoid.
**Recommended fix:** 
```py
# apps/api/tests/test_admin_endpoints.py
from pathlib import Path

def test_swarm_memory_root_points_to_repo():
    from app.routers import admin
    expected = Path(__file__).resolve().parents[3] / "memory" / "swarm"
    assert admin.SWARM_MEMORY_DIR == expected
```
**Sprint slot:** S2
**Estimated effort:** 0.75h
**Dependencies:** F-07
**Test added:** yes

### F-09 — frontend security headers omit CSP and HSTS entirely
**Severity:** P2
**Specialist:** Security
**Surface:** `C:\Projects\VOLAURA\apps\web\next.config.mjs:17-29`
**Evidence:** 
```js
17:   async headers() {
18:     return [
19:       {
20:         source: "/(.*)",
21:         headers: [
22:           { key: "X-Frame-Options", value: "DENY" },
23:           { key: "X-Content-Type-Options", value: "nosniff" },
24:           { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
25:           { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
26:         ],
27:       },
28:     ];
29:   },
```
**Impact if unfixed:** The API layer has CSP+HSTS middleware, but the user-facing Next.js surface does not send equivalent protections. That leaves the browser shell relying on platform defaults and weakens mitigation against inline script injection, protocol downgrades, and third-party widget drift on the highest-traffic surface in the ecosystem.
**Recommended fix:** 
```js
// apps/web/next.config.mjs
headers: [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains; preload" },
  { key: "Content-Security-Policy", value: "default-src 'self'; img-src 'self' data: https://*.supabase.co; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" },
]
```
**Sprint slot:** S2
**Estimated effort:** 1h
**Dependencies:** CSP validation against Vercel/Supabase assets
**Test added:** no

### F-10 — CI secret scan ignores `scripts/` and `supabase/`, leaving two code-bearing trees outside the only automated secret check
**Severity:** P2
**Specialist:** Security
**Surface:** `C:\Projects\VOLAURA\.github\workflows\ci.yml:96-107`
**Evidence:** 
```yaml
96:       - name: Check for secrets in code
97:         run: |
98:           # Simple secret detection — block commits with API keys
99:           if grep -rn "sk-[a-zA-Z0-9]\{20,\}" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.env" apps/ packages/ 2>/dev/null; then
103:           if grep -rn "AIza[a-zA-Z0-9_-]\{35\}" --include="*.ts" --include="*.tsx" --include="*.py" apps/ packages/ 2>/dev/null; then
107:           echo "No secrets detected."
```
**Impact if unfixed:** The repository contains executable Python in `scripts/` and SQL/config payloads in `supabase/`, but the only automated secret gate never scans them. A leaked service token in an operational script or migration helper can sail through CI while `apps/` and `packages/` still look clean.
**Recommended fix:** 
```yaml
# .github/workflows/ci.yml
if grep -rn "sk-[a-zA-Z0-9]\{20,\}" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.sql" --include="*.env" apps/ packages/ scripts/ supabase/ 2>/dev/null; then
  echo "::error::Possible API key found in source code!"
  exit 1
fi
if grep -rn "AIza[a-zA-Z0-9_-]\{35\}" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.sql" apps/ packages/ scripts/ supabase/ 2>/dev/null; then
  echo "::error::Possible Google API key found in source code!"
  exit 1
fi
```
**Sprint slot:** S2
**Estimated effort:** 0.5h
**Dependencies:** none
**Test added:** no

### F-11 — the pgTAP RLS suite covers only six named tables in a 63-table public schema
**Severity:** P1
**Specialist:** RLS
**Surface:** `C:\Projects\VOLAURA\supabase\tests\README.md:3-4`; `C:\Projects\VOLAURA\supabase\tests\README.md:32-38`; `C:\Projects\VOLAURA\supabase\tests\01_baseline_rls_enabled.test.sql:10-78`
**Evidence:** 
```md
3: Minimum viable test suite. Grows with every new policy.
32: ## Existing tests
34: - `01_baseline_rls_enabled.test.sql` — every critical table has `relrowsecurity` AND
36: - `02_registrations_trigger.test.sql` — asserts the 20260415124500 trigger blocks the
```
```sql
10: SELECT plan(14);
15:     (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.profiles'::regclass),
26:     (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.aura_scores'::regclass),
37:     (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.registrations'::regclass),
48:     (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.assessment_sessions'::regclass),
59:     (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.events'::regclass),
70:     (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.organizations'::regclass),
```
**Impact if unfixed:** The workflow named `RLS tests` gives a false sense of coverage. In practice it validates RLS flags on six tables plus one trigger regression, leaving dozens of live public tables and all policy-pair semantics untested. Any future migration can quietly weaken access on non-covered tables and still merge behind a green pgTAP badge.
**Recommended fix:** 
```sql
-- supabase/tests/03_all_public_tables_force_rls.test.sql
BEGIN;
SELECT plan(1);

SELECT is(
  (
    SELECT count(*)::int
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind = 'r'
      AND c.relrowsecurity = false
  ),
  0,
  'all public tables have relrowsecurity=true'
);

SELECT * FROM finish();
ROLLBACK;
```
**Sprint slot:** S1
**Estimated effort:** 2h
**Dependencies:** schema inventory
**Test added:** yes

### F-12 — obligations anomaly watcher ignores `in_progress` obligations even though the schema and list RPC treat them as active
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\\VOLAURA\\apps\\api\\app\\services\\error_watcher.py:143-147`; `C:\Projects\\VOLAURA\\supabase\\migrations\\20260418170000_atlas_obligations.sql:21-30`; `C:\Projects\\VOLAURA\\supabase\\migrations\\20260418170000_atlas_obligations.sql:169-172`
**Evidence:** 
```py
143:             await db.table("atlas_obligations")
144:             .select("id", count="exact")
145:             .eq("status", "open")
146:             .lt("deadline", thirty_days_out)
147:             .execute()
```
```sql
21:     status TEXT NOT NULL DEFAULT 'open',               -- open | in_progress | completed | deferred | cancelled
29:     CONSTRAINT obligations_status_check
30:         CHECK (status IN ('open','in_progress','completed','deferred','cancelled')),
169:     FROM public.atlas_obligations o
170:     WHERE o.status IN ('open','in_progress')
171:       AND (o.deferred_until IS NULL OR o.deferred_until < now())
```
**Impact if unfixed:** Once an obligation receives partial proof or any manual progress update, it can move to `in_progress` and disappear from the watcher’s anomaly budget even if the deadline is still approaching. That creates a blind spot exactly when legal/compliance items become active but unfinished.
**Recommended fix:** 
```py
due_soon = (
    await db.table("atlas_obligations")
    .select("id", count="exact")
    .in_("status", ["open", "in_progress"])
    .lt("deadline", thirty_days_out)
    .execute()
)
```
**Sprint slot:** S3
**Estimated effort:** 0.5h
**Dependencies:** update `test_error_watcher.py`
**Test added:** yes

## web / type safety / design-law violations

### F-13 — event creation flow suppresses Zod type inference with `as any`
**Severity:** P2
**Specialist:** Type Safety
**Surface:** `C:\Projects\VOLAURA\apps\web\src\app\[locale]\(dashboard)\events\create\page.tsx:103-106`
**Evidence:** 
```ts
103:   const form1 = useForm<Step1Data>({ resolver: zodResolver(step1Schema as any), defaultValues: step1Data ?? undefined });
104:   const form2 = useForm<Step2Data>({
105:     resolver: zodResolver(step2Schema as any),
106:     defaultValues: step2Data ?? { is_public: true, required_min_aura: 0 },
```
**Impact if unfixed:** The live event-creation path throws away the very schema typing it relies on for validation. Any drift between `Step1Data` / `Step2Data` and the Zod schemas will compile cleanly and fail only at runtime, which is exactly the class of regression strict-mode is supposed to catch.
**Recommended fix:** 
```ts
const form1 = useForm<Step1Data>({
  resolver: zodResolver(step1Schema),
  defaultValues: step1Data ?? undefined,
});

const form2 = useForm<Step2Data>({
  resolver: zodResolver(step2Schema),
  defaultValues: step2Data ?? { is_public: true, required_min_aura: 0 },
});
```
**Sprint slot:** S3
**Estimated effort:** 0.5h
**Dependencies:** none
**Test added:** no

### F-14 — assessment completion page ships a 1000ms pulse, breaking the 800ms animation ceiling
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\web\src\app\[locale]\(dashboard)\assessment\[sessionId]\complete\page.tsx:344-349`
**Evidence:** 
```tsx
344:           {score >= 75 && !prefersReducedMotion && (
345:             <motion.div
346:               initial={{ scale: 1, opacity: 0.7 }}
347:               animate={{ scale: 1.6, opacity: 0 }}
348:               transition={{ duration: 1.0, delay: 0.4, ease: "easeOut" }}
349:               className="absolute inset-0 rounded-full ring-4 bg-primary/10 pointer-events-none"
```
**Impact if unfixed:** The high-salience completion surface violates Foundation Law 4 on one of the most emotionally loaded transitions in the product. Neurodivergent users get a longer pulse exactly at the moment the app is trying to celebrate a result, increasing vestibular/noise risk where the Constitution requires calmness.
**Recommended fix:** 
```tsx
transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
```
**Sprint slot:** S2
**Estimated effort:** 0.25h
**Dependencies:** none
**Test added:** no

### F-15 — AURA reveal overlay runs 1.4s repeated motion, 75% over the Constitution ceiling
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\web\src\app\[locale]\(dashboard)\aura\page.tsx:144-147`
**Evidence:** 
```tsx
144:       <motion.div
145:         animate={prefersReducedMotion ? {} : { scale: [1, 1.08, 1], opacity: [0.6, 1, 0.6] }}
146:         transition={prefersReducedMotion ? {} : { repeat: 5, duration: 1.4, ease: "easeInOut" }}
147:         className="text-6xl mb-6"
```
**Impact if unfixed:** The dedicated “revealing AURA” overlay magnifies one of the most visible dashboard transitions into a repeated 1.4-second pulse sequence. That breaks the same motion ceiling the design system encodes in CSS tokens and makes the product’s flagship identity screen violate its own safety law.
**Recommended fix:** 
```tsx
transition={prefersReducedMotion ? {} : { repeat: 2, duration: 0.6, ease: "easeOut" }}
```
**Sprint slot:** S2
**Estimated effort:** 0.25h
**Dependencies:** none
**Test added:** no

### F-16 — badge glow animation repeats for 2 seconds, contradicting the motion contract in the shared design system
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\web\src\components\aura\badge-display.tsx:68-77`
**Evidence:** 
```tsx
68:         transition={
69:           prefersReducedMotion
70:             ? {}
71:             : tier === "platinum" || tier === "gold"
72:             ? { repeat: 3, duration: 2, ease: "easeInOut" }
73:             : {}
74:         }
```
**Impact if unfixed:** The reusable badge component bakes an overlong motion profile into every premium achievement surface. Because this component is shared, the violation is multiplicative: every future screen that reuses `BadgeDisplay` inherits a 2-second glow even if the page itself tries to stay within the constitutionally safe motion range.
**Recommended fix:** 
```tsx
? { repeat: 2, duration: 0.6, ease: "easeOut" }
```
**Sprint slot:** S2
**Estimated effort:** 0.25h
**Dependencies:** none
**Test added:** no

### F-17 — tribe waiting state spins forever on a 2-second loop
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\web\src\components\dashboard\tribe-card.tsx:62-67`
**Evidence:** 
```tsx
62:           <motion.span
63:             className="text-2xl"
64:             aria-hidden="true"
65:             animate={prefersReducedMotion ? {} : { rotate: 360 }}
66:             transition={prefersReducedMotion ? {} : { repeat: Infinity, duration: 2, ease: "linear" }}
67:           >
```
**Impact if unfixed:** The tribe-pool waiting state exposes users to infinite motion in a dashboard widget that can persist across refreshes. Reduced-motion users are protected, but everyone else gets a non-terminating spinner that directly violates the repo-wide 800ms guidance and adds background agitation to a page that is supposed to reduce shame and friction.
**Recommended fix:** 
```tsx
animate={prefersReducedMotion ? {} : { rotate: [0, 180, 360] }}
transition={prefersReducedMotion ? {} : { repeat: 1, duration: 0.6, ease: "easeOut" }}
```
**Sprint slot:** S2
**Estimated effort:** 0.25h
**Dependencies:** none
**Test added:** no

### F-18 — runtime product accent tokens still encode the pre-reconciliation palette
**Severity:** P2
**Specialist:** Architecture
**Surface:** `C:\Projects\VOLAURA\apps\web\src\app\globals.css:132-136`
**Evidence:** 
```css
132:   --color-product-volaura:            #7C5CFC;
133:   --color-product-mindshift:          #3B82F6;
134:   --color-product-lifesim:            #F59E0B;
135:   --color-product-brandedby:          #EC4899;
136:   --color-product-atlas:              #10B981;
```
**Impact if unfixed:** The live runtime still declares MindShift as blue and Atlas as emerald in the root product-token layer. That codifies the exact canon drift the design reconciliation pass was trying to remove, so every future component that consumes these tokens will keep pulling the old ecosystem identity back into production.
**Recommended fix:** 
```css
--color-product-volaura:   #7C5CFC;
--color-product-mindshift: #10B981;
--color-product-lifesim:   #F59E0B;
--color-product-brandedby: #EC4899;
--color-product-atlas-system: #5EEAD4;
```
**Sprint slot:** S4
**Estimated effort:** 0.5h
**Dependencies:** CEO sign-off on final Atlas system accent
**Test added:** no
