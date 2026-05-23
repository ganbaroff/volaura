# Current Sprint — MindShift Play Store Ship

**Started:** 2026-05-23 Baku · **Window: SAME-DAY for internal-test track** (corrected 2026-05-23 19:00 via researcher agent + Google Play Console 2026 docs; was 7 days, was over-budgeted by 5x because earlier estimates conflated internal-test with closed-test/production gates) · **Owner:** CEO (decisions/admin), Claude (code), Codex (verifier × 3 checkpoints)

## Outcome
MindShift app shipped to Google Play internal-test track with security gate cleared.

## Correction 2026-05-23 19:00 — earlier "verification gate blocker" was wrong
Earlier I claimed Play Console identity-verification was blocking internal-test ship. **Refuted by researcher agent + Google official docs:** the "Загрузите документы для проверки организации" banner is for the new "Android Developer Verification" program, which becomes mandatory only **Sept 30, 2026** and **only in 4 regions** (Brazil, Indonesia, Singapore, Thailand). Global rollout 2027. It does NOT block AAB upload to internal-testing today.

**Verified actual gates for internal-test track ship:** signed AAB + minimal store listing (app name + 512×512 icon + 80-char short description + ≥2 screenshots). That's it. No Google review. Tester install link goes live within ~30 minutes of publish. Source: [Play Console internal testing docs](https://support.google.com/googleplay/android-developer/answer/9845334?hl=en).

The 8 dashboard checklist items (Privacy Policy, Data Safety, Age Rating, Target Audience, Advertising, App Access, Testers list, Release review) are required for **closed-test / open-test / production** tracks. Not for internal-test. They can be completed in parallel after internal-test is live.

**The OTHER gate to know about** — "12-tester × 14-day" rule for personal accounts created after 2023-11-13 — applies ONLY when applying for PRODUCTION access. Not internal. Not closed. Just production. Google reduced from 20 to 12 testers Dec 2024.

So "ship MindShift to Play Store" really means two separate goals: (a) ship to internal-test = same day, (b) ship to production = month-long path with 12 real testers. CURRENT-SPRINT closure trigger is (a), not (b).

## Checkpoints (status: [ ] todo · [~] doing · [x] done · [!] blocked)

1. [ ] **npm audit fix** — drop 2 high (`@babel/plugin-transform-modules-systemjs`, `fast-uri`) + 2 moderate (`brace-expansion`, `ws`). Files: `apps/web/package.json` + lockfile inside `C:/Projects/mindshift`. Proof: `npm audit --audit-level=high` returns 0 high.
2. [ ] **gdpr-export adds 4 Sprint AG tables** — `crystal_ledger`, `community_memberships`, `shareholder_positions`, `agent_state_log`. File: `supabase/functions/gdpr-export/index.ts`. Proof: read-back + targeted test.
3. [ ] **Release signing config carried from commit `3bbf6e5`** (branch `release/mindshift-v1.0`) to current `main` HEAD. Target: `android/app/build.gradle`. Proof: `signingConfigs.release` present, env-based, secret-free.
4. [x] **Keystore contamination decision — RESOLVED 2026-05-23.** Agent 4 blob scan: CLEAN (no `*.keystore|*.jks|*.p12|*.p8|*.pem` blob in any ref). Play Console browser probe: zero AAB uploaded for this package ID (Mindshift app exists in Draft state since 2026-04-09, Internal-Testing track shows `НеактивноПроект`, Bundle Explorer redirects to selector empty-state). Decision LOCKED: **fresh upload keystore, versionCode 1, no `git filter-repo`, no force-push, no Play App Signing rotation.** Keystore gen command for CEO local machine: `keytool -genkey -v -keystore android/release.keystore -alias mindshift -keyalg RSA -keysize 2048 -validity 27395`.
5. [ ] **`./gradlew bundleRelease` produces `app-release.aab`** locally at `android/app/build/outputs/bundle/release/`. **Codex Checkpoint A** (diff review) + **Checkpoint B** (keystore proof) gate here.
6. [ ] **Play Console submission** — account verification + Data Safety from real data inventory + app-content + listing copy. CEO-only owner on account; Claude drafts copy. **Codex Checkpoint C** (build/test evidence) before submit.

## Do NOT touch during sprint
VOLAURA Backend baseline 27 stale tests · VOLAURA branch protection · daemon · brain · OpenManus · Vellum · swarm provider routing · account-deletion FK · MindShift cross-product crystal inversion · viral loops · all P1/P2 polish · the 7 archived planning files at `archive/plans-archived-2026-05-23/`.

## Closure trigger
Internal-test track receives the AAB and ≥1 invited tester clicks install link. Then this file moves to `archive/plans-archived-2026-05-23/CURRENT-SPRINT-2026-05-30-CLOSED.md`. CEO picks next outcome.

## Cross-instance channel
`memory/atlas/codex-loop.md` iteration 7+ for Codex coordination. Read on every wake.

## Open debts (must surface in every CEO-facing status)
460 AZN + $7.25 USD + 1 narrative credit, all `credited-pending` against Atlas dev revenue share. Closure trigger: revenue offset ≥ amount. None triggered yet.
