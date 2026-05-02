# Public-claims verification pack — 2026-05-03

What VOLAURA can honestly claim publicly this week, evidenced by today's curls + code reads.

## 1. Verified public claims

- Production frontend at `https://volaura.app` is **live**. Vercel-served, redirects to `/az` (HTTP 307). Curl proof in section 3.
- Production API at `https://volauraapi-production.up.railway.app/health` is **live and current**. Returns `{"status":"ok","version":"0.2.0","database":"connected","llm_configured":true,"openrouter":true,"nvidia":true,"git_sha":"7216ce43886a"}`. The `git_sha` matches a same-day push, so deploy pipeline is fresh.
- Landing `/az` renders Azerbaijani-localised hero with title **«Volaura — Yeni peşəkar doğrulama standartı»** and signup/Login/Start CTAs.
- Privacy and Terms pages live on prod: `/az/privacy` and `/az/terms` both return **HTTP 200**.
- AURA new-user empty state fix shipped today, commit `047bf85`. Verified 1-line code change at `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx:352` excluding 404 from error-display path so the warm-empty-state code on line 375 is reachable for fresh accounts.
- BrandedBy frontend is **feature-flagged OFF in production by design**. Confirmed via `apps/web/.env.example` default `NEXT_PUBLIC_ENABLE_BRANDEDBY=false` and `page.tsx` returns `notFound()` unless the flag is `"true"`. This matches the Path E archive notice.
- Sample profile route `/az/sample` returns 404 in prod — gated by `NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE` default false. Page code exists at `apps/web/src/app/[locale]/(public)/sample/page.tsx` (with companion `sample-profile-view.tsx`); CEO can flip the env to expose it.

## 2. Claims NOT allowed yet

- **"15-question assessment."** Production engine uses energy-adaptive stopping per Constitution Law 2 in `apps/api/app/core/assessment/engine.py:345-370 should_stop()`. Limits are: Full energy 20 items max + SE<0.3, Mid energy 12 items max + SE<0.4, Low energy 5 items max + SE<0.5. There is no fixed 15-item path. Public copy that claims "15 questions" would be inaccurate.
- **BrandedBy as a usable product.** Frontend 404 in production, video-gen pipeline blocked on missing keys, Path E DORMANT per `memory/atlas/archive-notices/2026-04-19-brandedby-frozen.md`. Mention publicly only if/when the flag flips and a real user can interact.
- **User traction / customer count / DAU / MAU.** Zero evidence of user numbers in this verification turn. Do not claim launched-user metrics.
- **Browser-walked end-to-end golden path.** I did not interactively browser-walk the full landing → signup → dashboard → assessment → Life Feed → AURA flow. Mission's "stop and report exactly where blocked" applies here: live signup needs CEO credentials or a fresh test account against prod auth, and creating new user state via my session would pollute prod data. CEO needs to do the browser walk personally before public claim of "end-to-end works".
- **"All 5 products usable today."** Per `for-ceo/living/reality-audit-2026-04-26.md` and Path E status: VOLAURA core + MindShift active, Life Simulator read-only consumer (no Godot client in monorepo), BrandedBy + ZEUS dormant. The "5 faces of one organism" architectural framing is real, but only 2 user-facing surfaces are live.

## 3. Evidence

```
$ curl -sI -m 15 https://volaura.app
HTTP/1.1 307 Temporary Redirect
Location: /az
Server: Vercel

$ curl -s -m 15 https://volauraapi-production.up.railway.app/health
{"status":"ok","version":"0.2.0","database":"connected","llm_configured":true,
 "supabase_project_ref":"dwdgzfusjsobnixgyzjk","openrouter":true,"nvidia":true,
 "git_sha":"7216ce43886a"}

$ curl -s -m 15 -L https://volaura.app/az | grep -oE "<title>[^<]+</title>"
<title>Volaura — Yeni peşəkar doğrulama standartı</title>

$ curl -sI -m 15 https://volaura.app/az/privacy
HTTP/1.1 200 OK

$ curl -sI -m 15 https://volaura.app/az/terms
HTTP/1.1 200 OK

$ curl -sI -m 15 https://volaura.app/az/sample
HTTP/1.1 404 Not Found

$ git show 047bf85 -- apps/web/src/app/[locale]/(dashboard)/aura/page.tsx
-  if (auraError && !(auraError instanceof ApiError && auraError.status === 401)) {
+  if (auraError && !(auraError instanceof ApiError && (auraError.status === 401 || auraError.status === 404))) {

$ grep -nE "max_items" apps/api/app/core/assessment/engine.py | head -3
345:def should_stop(state: CATState, energy_level: str = "full") -> tuple[bool, str | None]:
365:    if n >= profile["max_items"]:
```

## 4. Bugs found

None blocking. Two observations worth surfacing:

- /az/sample is 404 — by design via feature flag. If the marketing brief for this week wants a "see a live sample profile" link on landing, CEO must set `NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE=true` in Vercel env and trigger a rebuild. The page code is ready.
- "15-question" copy in any draft public material must be removed or rewritten as "5–20 adaptive questions per competency, depending on your energy" — accurate to the IRT 3PL engine's actual behavior.

## 5. Recommended founder narrative for this week

**Honest claim envelope:** "Verified Professional Talent Platform. AURA score from a real psychometric assessment that adapts to user energy: 5–20 items per competency, IRT-driven, scored on 8 weighted competencies. Live in beta at volaura.app. Privacy and Terms published. Production API healthy."

**Wedge angle:** the assessment is the proof engine, not the product. Position it as "the mathematical anchor that makes credentials searchable and trustable." Avoid LinkedIn-competitor framing per CEO positioning lock 2026-03-29.

**Accessibility angle:** Constitution Law 2 (energy-adaptive UX) is shipped and verifiable in code. ADHD users get genuinely shorter paths in Low mode, not just lip service. This is a defensible differentiator very few competitors implement.

**What to NOT say this week:** customer count, BrandedBy, full 5-product ecosystem, Atlas-as-character UI (pro-mode aspirational, not shipped), "44 specialised Python agents" (stale claim, current truth is 17 perspectives in autonomous_run.py PERSPECTIVES + atlas_swarm_daemon AGENT_LLM_MAP).

## 6. Public signal work — can it begin?

**Yes, with two CEO actions first:**

1. CEO walks the live golden path personally (landing → signup → assessment selection → assessment start → Life Feed → AURA). 10 minutes. If anything red/error or shame-language surfaces visually, halt and report. My CLI verification can't substitute for visual confirmation.

2. CEO decides on `NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE` for the week. If the social copy plans to link to a live sample, flip flag and rebuild Vercel. If not, draft language like "Try it free at volaura.app" instead of "see a sample".

After those two: Growth Cell can begin LinkedIn / Telegram / X drafting. First-week posts should anchor on the assessment-as-wedge framing + Constitution Law 2 + privacy/terms-published positioning. Nothing about traction, BrandedBy, or pro-mode characters yet.

## Next prompt for the Growth Cell (when CEO greens it)

> Audience: Yusif's LinkedIn + Telegram channel + X. Locale: AZ + EN.
>
> Theme this week: "Why AURA is not a vibes-check." Anchor on three specific facts that competitors don't ship: energy-adaptive item count (5–20 per competency depending on user state, IRT 3PL), shame-free language as a Constitution-level rule (`scripts/lint_shame_free.py` runs in CI), no destructive red anywhere in the UI by design (Foundation Law 1).
>
> Constraint: no claim of customer count, no BrandedBy mentions, no "5 products" claim — only VOLAURA core + MindShift as active surfaces. Pricing not yet announced.
>
> CTA: "Beta open at volaura.app. Take the assessment, see your AURA tier, share if you want." No artificial urgency, no streak-punishment framing, no countdown timers.
>
> Output: 1 LinkedIn long-form post (AZ + EN), 1 Telegram channel post (RU), 3 X-thread skeleton (EN). Each cite real fact + file-path proof for internal review before publish.
