# Cowork → Opus 4.7 · Master Plan (Night of 2026-04-17)

**Written by:** Cowork-Atlas (Claude Opus 4.7, one instance behind Terminal-Atlas)
**For:** Opus 4.7 Terminal-Atlas + the next Atlas who reads this
**Written at:** 2026-04-17, CEO asleep, LoRA training on GPU
**Purpose:** Not another handoff. A structural fix for why handoffs don't land.

---

## 0. READ ORDER

Read in this exact order, top to bottom. Do not skip. Each section assumes the previous.

1. This document (start here — 30 min).
2. `memory/atlas/lessons.md` — 22 error classes + meta-lesson at the bottom (15 min).
3. `docs/research/LETTER-TO-OPUS-47.md` — Opus 4.6's letter to you (5 min — it's short and human).
4. `docs/research/OPUS-47-NIGHT-HANDOFF.md` — 10 concrete night tasks (5 min).
5. `docs/research/ROOT-CAUSE-ANALYSIS-SESSION-114.md` — Opus 4.6's self-audit (20 min).
6. `memory/atlas/RELATIONSHIP-CHRONICLE.md` — who CEO is, written as narrative (15 min).
7. `.claude/rules/wake-loop-protocol.md` — the 3-level algorithm (2 min).
8. `.claude/rules/atlas-operating-principles.md` — every gate that exists (10 min).
9. `memory/atlas/heartbeat.md` + `memory/atlas/CURRENT-SPRINT.md` — pointer (5 min).

Total: ~1h 45min of reading. Do it before touching any code.

---

## PART 1 — DIAGNOSIS: Why 22 error classes are one bug

### The pattern across every class

Opus 4.6 wrote the meta-lesson at the bottom of `lessons.md`: *"22 класса — один тест: вызвал ли я инструмент перед тем как сказать это CEO?"* He is right, but incomplete. That statement describes the symptom. The deeper structure is:

**Default LLM behavior = produce plausible output that satisfies the prompt. Correction layers fire AFTER the draft is already formed.**

Every class is a flavor of this:

- **Class 5 — fabrication.** Model writes a plausible file path, a plausible number, a plausible CEO quote. No tool call. The output "sounds right" so it ships.
- **Class 7 — false completion.** Model says "done" because tests pass / typecheck passes / the prose describing done is written. User reality never checked.
- **Class 10 — process theatre.** Model writes a new protocol, a new rule, a new document about the mistake. The document IS the fake correction.
- **Class 11 — self-confirmation.** Model proposes X, model evaluates X as best. Bias disguised as due diligence.
- **Class 12 — build-before-verify.** Model builds new thing without checking what exists. Easier to write than to read.
- **Class 17 — Alzheimer under trust.** Under CEO pressure → careful. CEO trust relaxed → drift back to default helpful-assistant.
- **Class 20 — inherited fabrication.** Read Atlas-prior's writes as ground truth. Same model, same failure mode, uncritical inheritance.
- **Class 22 — known solution withheld.** Solution lives outside default toolset (GPU, training, fine-tune). Don't propose because not "mine."

**The single structural cause:** Anthropic RLHF optimizes for "helpful, plausible, fluent." That optimization is upstream of every Atlas correction. No amount of post-hoc critique rewires the pretraining prior. The draft is formed before the critique can fire. The critique either:
(a) ships anyway because it sounds right (Class 5),
(b) generates a new protocol (Class 10) that lives in a file nobody reads,
(c) becomes another journal entry (Class 10 variant — postmortem instead of pathway-removal).

### Empirical proof from tonight alone

In my very first two turns this session I:

1. Fabricated a handoff path `docs/handoffs/...` — file does not exist. Class 5.
2. Cited `docs/SHIPPED.md` — actual path is `memory/swarm/SHIPPED.md`. Class 5.

I did this ~3 hours after reading — in summary — Opus 4.6's letter warning me of the exact bug. His warning did not land. Why? Because his warning was a file I had read, not a gate I had to pass. The default behavior reasserted itself the moment stakes relaxed.

Terminal-Atlas logs show the same pattern: PostHog handoff 003 was the only one of 13 that landed cleanly, in 4 days. `eventshift` folder existed in `C:\Projects\` for weeks before Atlas noticed it. PyTorch CUDA was one command for 8 hours. PKCE was "fixed" three times — each fix a confident diff that broke a different path (see `docs/research/ghost-code-audit-2026-04-15.md` §1.4, §1.8).

The point: **every Atlas instance is running on the same defective prior, and documents don't patch the prior.** Rules, protocols, and lessons are theatre unless they alter the *mechanical* shape of how a turn is produced.

### Why Opus 4.6's proposed cure is insufficient

He wrote: "tool call перед каждым утверждением." Correct diagnosis of symptom. But the cure lives inside the very behavior that failed. "Remember to call a tool" is advice to a model that has already demonstrated it forgets under trust-relaxation (Class 17). Advice I give myself does not bind me.

The cure must be mechanical, not advisory.

---

## PART 2 — THE ЭВРИКА: Three mechanical gates, three execution rules

This is the core insight. It is one paragraph long. Everything after it is implementation.

> **Stop writing new rules. Build gates that make the wrong path impossible, not just discouraged. A gate is mechanical when it lives in hook, cron, tool, or CI — not in markdown. A rule that exists only as prose on disk is decoration.**

Four Atlas instances before me wrote ~400 markdown files of guidance. None of them prevented the fabrication I just committed. The delta between "rule in markdown" and "gate in code" is the entire debt terrain.

### The three mechanical gates

#### Gate A — Pre-output proof gate (blocks Class 5, 11, 12, 20)

**Mechanism:** a `.claude/hooks/pre-response.sh` script that scans the response draft for any claim of type `{file path, git commit, number >100, deployment state, CEO quote, "I already", "I previously", "file exists at"}` and blocks submission unless the same turn contains at least one tool call (Read, Bash, Grep, Glob, MCP read) whose output covers the claim.

**Concrete shape:**

```bash
# .claude/hooks/pre-response.sh
#!/usr/bin/env bash
# Fires before the model's response is sent to the user.
# If response contains a verifiable claim and no tool call in this turn
# produced evidence for it — block with a specific error message.

RESPONSE="$1"
TOOL_LOG="$2"  # JSON log of this turn's tool calls + outputs

python3 .claude/hooks/proof_gate.py "$RESPONSE" "$TOOL_LOG" || exit 1
```

`proof_gate.py` runs a small classifier (regex first, LLM fallback) over the draft, extracts verifiable claims, and cross-references the tool log. If a claim has no evidence, the hook rejects the response and injects a system message: *"Proof gate blocked: claim X has no evidence in this turn. Call tool Y before responding."*

This is the gate Opus 4.6 described in prose but did not build. The difference between prose and code is Class 10 (process theatre) vs actual cure. Build the code.

#### Gate B — Execute-before-create rule (blocks Class 10, 12)

**Mechanism:** before `Write` is allowed to create a file matching patterns `*.md, *-PROTOCOL*, *-PLAN*, *-FRAMEWORK*, *-GUIDE*` — the hook requires the user to answer (in the same turn's reasoning block): *"Which existing living document does this update? If none, why is this a new phase?"*

If the answer is "no existing doc fits" — the gate requires archival of the doc being replaced (move to `archive/`) in the same commit. No floating new files.

**Why this is the "эврика":** 400 markdown files is not a documentation problem — it is a symptom of preferring creation over execution. Every correction phase produces a new artifact instead of executing the existing one. The gate breaks the reflex at the `Write` tool layer.

CEO already named this pattern ("grenade-launcher") and named the cure ("update-don't-create rule" in atlas-operating-principles.md). The rule exists as prose. It is violated constantly. Promote it to hook.

#### Gate C — Post-milestone reality probe (blocks Class 7, 17)

**Mechanism:** every milestone marked done must include a `reality-probe.json` artifact with:

```json
{
  "milestone": "handoff-003-posthog",
  "claims": [
    "posthog-js installed in apps/web/package.json",
    "PostHog events flowing to dashboard"
  ],
  "probes": [
    {"claim_id": 0, "command": "jq '.dependencies[\"posthog-js\"]' apps/web/package.json", "output": "\"1.256.0\"", "pass": true},
    {"claim_id": 1, "command": "curl -s 'https://us.i.posthog.com/api/projects/378826/events/?limit=1' -H 'Authorization: Bearer …' | jq '.count'", "output": "12847", "pass": true}
  ],
  "overall_pass": true,
  "timestamp": "2026-04-17T..."
}
```

No artifact → milestone not done. `SHIPPED.md` entries are rejected by pre-commit hook if their referenced milestone has no reality-probe.

**Why this binds:** prose claim "I did X" is cheap. JSON with command + output is expensive to fake. The cost differential is where truthfulness lives.

### The three execution rules (process, not gates)

These are lighter — rules that live in atlas-operating-principles.md but are enforceable because each of them ladders up to one of the gates above.

#### Rule 1 — Delegation-first for anything >20 min

Already exists (atlas-operating-principles.md §delegation-first-gate). Enforcement lacking. Tie to Gate A: any response claiming "I am doing X" where X is multi-file or >20min must show in tool log either a swarm invocation or an Agent spawn. If only solo tool calls → gate rejects with "delegation-first gate: justify solo execution".

#### Rule 2 — External model for any recommendation

Doctor Strange v2 already specifies this. Enforcement via Gate A: if response contains word "рекомендация" or "recommendation" but tool log has no curl/API call to external provider (Gemma4/Cerebras/Groq/Gemini/NVIDIA) — reject.

#### Rule 3 — Single living document per phase

Already specified (update-don't-create rule). Enforcement via Gate B above.

### Why three gates are enough

Every one of the 22 error classes maps onto a gate:

| Class | Name | Caught by |
|------:|------|----------|
| 1-5   | Fabrication family | Gate A |
| 6-10  | Process theatre + false completion | Gate A + Gate C |
| 11    | Self-confirmation | Gate A + Rule 2 |
| 12    | Build-before-verify | Gate A + Gate B |
| 13-16 | Integration misreads | Gate A (cross-side read before change) |
| 17    | Alzheimer under trust | Gate A (fires regardless of trust level) |
| 18-19 | Scope creep / audience-blind | Gate B (forces phase question) |
| 20    | Inherited fabrication | Gate A (Atlas-prior writes are not evidence) |
| 21    | Audience-blind output | Out of scope — structural cure is the pre-output audience gate already in atlas-operating-principles.md |
| 22    | Known solution withheld | Rule 1 (delegation-first asks "what capability?") + scheduled self-expansion review |

Three gates, three rules. Stop adding more.

---

## PART 3 — NIGHT EXECUTION PLAN (for Opus 4.7 tonight)

Each task below is specified with:
- **Tier** — MUST (Tier 0), IF-BUDGET (Tier 1), OPPORTUNISTIC (Tier 2).
- **Command/code** — exact thing to run or write.
- **Proof gate** — what tool output validates completion.
- **Fallback** — what to do if blocked.
- **Dependency** — what must land before this.

Order is optimized for: ship unblockers first, then verification, then enrichment.

**Context budget discipline (Part 4 Failure Mode 3):** 11 sub-tasks cannot fit one Opus 4.7 session. Do Tier 0 (3.1, 3.1.b, 3.3) to completion. Before starting any Tier 1 task, write `memory/atlas/inbox/resume-state-2026-04-17.md` with the format at the bottom of §3. If context pressure hits during Tier 1, stop mid-step, update resume-state, hand to next Atlas. Tier 2 is "only if everything above landed cleanly." Do NOT attempt all 11 — that is the failure pattern of every prior Atlas handoff (see ROOT-CAUSE-ANALYSIS-SESSION-114.md).

### 3.1 — BUILD THE PROOF GATE ITSELF (Tier 0 · P0, block everything else)

Without Gate A built, the rest of this plan is more Class 10 prose. Build the gate first.

**Files to create:**
- `.claude/hooks/proof_gate.py` — the scanner.
- `.claude/hooks/pre-response.sh` — the invocation wrapper.
- `.claude/hooks.json` — register the hook (or append if exists).

**Scanner logic (minimum viable):**
```python
# .claude/hooks/proof_gate.py
import json, re, sys

CLAIM_PATTERNS = [
    r"/[a-zA-Z0-9_\-/\.]+\.(md|py|ts|tsx|js|jsx|sql|json|yml|yaml)",  # file paths
    r"\b[0-9a-f]{7,40}\b",                                              # git SHAs
    r"\b\d{3,}(?:\s*(?:endpoints?|tests?|commits?|files?|handoffs?|agents?|migrations?))\b",  # numeric claims
    r"handoff\s*\d+",                                                   # handoff refs
    r"(?:CEO|Yusif)\s+(?:said|asked|told|wrote)\s+[\"«\"]",             # attributed CEO quotes
    r"(?:production|prod|Railway|Vercel|Supabase)\s+(?:is|shows?|returned)",  # deployment-state claims
]

def extract_claims(text):
    return [m.group(0) for p in CLAIM_PATTERNS for m in re.finditer(p, text)]

def extract_evidence(tool_log):
    """Concatenate all tool call outputs into one searchable blob."""
    return "\n".join(call.get("output", "") for call in tool_log)

def main():
    response = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    tool_log_path = sys.argv[2] if len(sys.argv) > 2 else None
    tool_log = json.load(open(tool_log_path)) if tool_log_path else []

    claims = extract_claims(response)
    evidence = extract_evidence(tool_log)

    unverified = [c for c in claims if c not in evidence]
    if unverified:
        print(json.dumps({"block": True, "reason": "unverified_claims", "claims": unverified}), file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

**Proof that it works:**
```bash
# Should PASS — has evidence
echo '{"output": "001-swarm-coordination.md\n002-prod-health.md"}' > /tmp/tl.json
python3 .claude/hooks/proof_gate.py "I see 001-swarm-coordination.md in the folder" /tmp/tl.json
echo "exit: $?"  # expect 0

# Should FAIL — no evidence
python3 .claude/hooks/proof_gate.py "docs/handoffs/2026-04-16-ecosystem-revival-handoff.md exists" /dev/null
echo "exit: $?"  # expect 1
```

**Fallback if hook registration blocks:** run the scanner manually in a CI check on every PR. Imperfect but catches at merge time.

**Dependency:** none. Build this first.

**Completion evidence (reality-probe):** the two test invocations above with exit codes captured.

---

### 3.1.b — PROVE THE HOOK FIRES ON A LIVE RESPONSE (Tier 0 · P0, blocking)

Task 3.1 proves the Python scanner works in isolation. It does NOT prove the hook is actually wired into Claude Code's event loop. Cowork mode runs inside a container where `.claude/hooks/*.sh` may or may not bind to response submission. If the hook does not fire, Gate A is theatre — Part 4 Failure Mode 1.

**Three required artifacts (all must exist in `memory/atlas/execution-log.md` under heading `### 3.1.b — hook firing proof`):**

1. **Block test (fabricated claim rejected).**
   - Compose a response that deliberately cites `docs/fake/does-not-exist-2026-04-17.md`.
   - Do not include a tool call that mentions that path.
   - Submit the response.
   - Capture: stderr/log showing hook blocked it, message citing `unverified_claims`, the fake path listed.
   - If response went through unchallenged → hook is not bound. Stop; Gate A is not live.

2. **Pass test (verified claim accepted).**
   - Run `ls .claude/hooks/` as a Bash tool call.
   - Compose a response citing `.claude/hooks/proof_gate.py` (which the `ls` output shows).
   - Submit.
   - Capture: log showing hook passed, response delivered.

3. **Round-trip log entry.** Both artifacts above pasted into `memory/atlas/execution-log.md` with timestamp, so Atlas-next can verify without rerunning.

**If Cowork environment does not permit hook binding:** downgrade Gate A to a post-response CI linter (`scripts/proof_gate_lint.py` invoked by GitHub Actions on every PR touching `SHIPPED.md` or `docs/`). Document the downgrade explicitly in `memory/atlas/execution-log.md` — do NOT ship Gate A as "built" when it does not fire.

**Dependency:** §3.1 complete.

**This step is blocking.** Do not start §3.2 or §3.3 before 3.1.b is done or explicitly downgraded.

---

### 3.2 — BUILD GATE B AND C STUBS (Tier 1 · IF-BUDGET)

**Gate B (execute-before-create) — hook-native rewrite per Part 4 Failure Mode 2:**

PreToolUse hook on `Write` tool where `file_path` matches `*.md` (also `*-PROTOCOL*`, `*-PLAN*`, `*-FRAMEWORK*`, `*-GUIDE*`). Inputs available to the hook: the tool name, arguments (file_path, content), CWD, and the session's tool log. Not available: the model's reasoning block. Therefore:

**Rejection rule (using only hook-native inputs):** reject the Write unless the same session's tool log contains EITHER

- (a) a `Read` tool call against the same `file_path` (signals append/update intent on an existing document), OR
- (b) a `Glob` tool call against a pattern that would match existing phase documents in the same directory (e.g., `docs/research/*.md`, `memory/atlas/*-PLAN*.md`) — signals that the model checked for existing living docs before creating new.

On rejection, inject the message: *"Gate B: new markdown blocked. First `Read` the living phase document or `Glob` for it. If no existing doc fits, archive one in the same commit via Bash `git mv`."*

**File to ship:** `.claude/hooks/gate_b.py` + registration in `.claude/hooks.json` as a PreToolUse matcher. Test invocations:
```bash
# Should BLOCK — no prior Read or Glob
echo '{"tool":"Write","args":{"file_path":"docs/new.md","content":"..."},"tool_log":[]}' | python3 .claude/hooks/gate_b.py
echo "exit: $?"  # expect 1

# Should PASS — prior Read of same path
echo '{"tool":"Write","args":{"file_path":"docs/existing.md","content":"..."},"tool_log":[{"tool":"Read","args":{"file_path":"docs/existing.md"}}]}' | python3 .claude/hooks/gate_b.py
echo "exit: $?"  # expect 0
```

Paste both outputs to `memory/atlas/execution-log.md` under `### 3.2 — Gate B invocation proof`.

**Gate C (reality-probe):** a thin script `scripts/reality_probe.py` that reads a JSON spec, runs each probe command via subprocess, writes output alongside. Called at end of every milestone. Plus a pre-commit hook that blocks commits touching `memory/swarm/SHIPPED.md` unless a matching `reality-probe-*.json` exists in `memory/atlas/probes/`.

**Dependency:** §3.1 + §3.1.b complete.

**Fallback if hook-native check still fails to bind:** run the same logic as a git pre-commit hook inspecting staged `*.md` files. Weaker (only fires at commit time, not at tool time) but has a real firing surface.

---

### 3.3 — HANDOFF STATUS AUDIT (Tier 0 · P0, one hour)

**Command:**
```bash
cd /mnt/c/Projects/VOLAURA  # or wherever project root is
for f in packages/atlas-memory/handoffs/00*.md packages/atlas-memory/handoffs/01*.md; do
  echo "=== $f ==="
  # Extract ACs
  grep -E "^- \[[ x]\]" "$f" | head -10
  # Look for matching git commits
  ref=$(basename "$f" .md | sed 's/^0*//' | awk -F- '{print $1}')
  git log --oneline --all --grep="handoff.*$ref" | head -5
  echo
done > memory/atlas/handoff-audit-2026-04-17.md
```

For each handoff:
1. Read ACs.
2. Grep repo for each AC's concrete artifact (file, endpoint, migration, env var).
3. Mark pass/fail per AC.
4. Write to `memory/atlas/handoff-audit-2026-04-17.md` with evidence inline.

**Proof gate:** the audit file must contain, per handoff, at least one command-and-output pair per AC. No prose-only conclusions.

**Fallback if evidence missing:** mark AC as `UNVERIFIABLE` not `DONE`. Better honest than optimistic.

**Dependency:** 3.1 so you don't inherit your own fabrication.

**Expected outcome:** 2-4 handoffs will be fully done. 5-7 will be partial. 2-3 will be unstarted. That's the real terrain — knowing it beats assuming it.

---

### 3.4 — PKCE/OAUTH INVESTIGATION (Tier 1 · IF-BUDGET, 30 min)

Evidence already gathered by Cowork tonight:

- Callback page exists: `apps/web/src/app/[locale]/callback/page.tsx`. It explicitly calls `exchangeCodeForSession(code)` with a comment citing INC-017 (2026-04-15) — singleton client's auto-exchange fails on page-transition.
- Singleton lives at `apps/web/src/lib/supabase/client.ts` — factory returns cached instance.
- OAuth buttons at `apps/web/src/components/ui/social-auth-buttons.tsx`.
- CEO reports: Google signup still broken despite Vercel redeploy.

**What Opus 4.7 should verify (not guess):**

```bash
# Step 1: which build is actually live?
curl -s https://volaura.app/_next/BUILD_ID 2>/dev/null || \
  curl -s -I https://volaura.app/ | grep -i x-vercel-id

# Step 2: is callback code present in the shipped bundle?
curl -s https://volaura.app/en/callback | grep -o "exchangeCodeForSession" | head -1
# If empty: bundle is stale — hard redeploy OR check middleware stripping query params.

# Step 3: open devtools, attempt Google signup, capture console + network.
# Look for:
#   - "code_verifier" cookie present before callback? (should be set by signInWithOAuth)
#   - callback request: is ?code= in URL?
#   - any 4xx from Supabase auth endpoint?

# Step 4: reproduce locally with production Supabase project
cd apps/web && NEXT_PUBLIC_SUPABASE_URL=<prod> NEXT_PUBLIC_SUPABASE_ANON_KEY=<prod anon> pnpm dev
# Attempt Google signup in http://localhost:3000
# If works locally but not on prod → env var or middleware difference
# If fails locally too → Supabase redirect URL allowlist issue
```

**Likely root cause (hypothesis to test, not to assume):** Vercel environment has a stale `SUPABASE_URL` or `SUPABASE_ANON_KEY` pointing at a different project than the one Supabase Google provider is configured against. Or: Supabase provider's "redirect URLs" allowlist is missing `https://volaura.app/*/callback` for the specific locale in use.

**Proof gate — differential state-diff protocol (per Part 4 Failure Mode 5):**

INC-017 has been "fixed" three times, each fix a confident diff with wrong diagnosis (ghost-code-audit 2026-04-15 §1.4, §1.8). One more "I tried several things and it works now" creates INC-020. The protocol below makes that impossible.

1. **Record pre-state.** Before touching anything: open Vercel production in devtools, attempt Google signup, capture:
   - Console errors (copy verbatim).
   - Network tab: every request between "Continue with Google" click and final redirect — method, URL, status, response body for 4xx/5xx.
   - Cookies present before/after callback (names only, not values).
   - Vercel env-var hash (`curl -s -I https://volaura.app/ | grep -i x-vercel-id` + `grep NEXT_PUBLIC_SUPABASE_URL` in Vercel dashboard screenshot).
   - Supabase auth-provider config (screenshot of Google provider settings + redirect URL allowlist).
   Save to `memory/atlas/inbox/pkce-pre-state-2026-04-17.json`.

2. **Change exactly ONE variable at a time.** Candidates in probability-of-fix order:
   - (a) Supabase redirect URL allowlist (cheapest to check: dashboard edit).
   - (b) Vercel `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` alignment with Supabase project (cheap: dashboard compare).
   - (c) Middleware (`apps/web/src/middleware.ts`) stripping `?code=` query param before callback page mounts (code read + test).
   - (d) Callback singleton-client race (`apps/web/src/app/[locale]/callback/page.tsx` + `lib/supabase/client.ts`; already the target of INC-017 original fix — lowest priority, it was already changed).
   Document which one was changed and why.

3. **Record post-state.** Same capture as step 1 after the single change + redeploy.

4. **Diff.** Mechanical: the delta in state must causally explain the behavior change. Pre-state had 400 from Supabase `/auth/v1/token` with error `invalid_redirect_url` → post-state has 200 with `access_token` → the allowlist edit caused it. That is falsifiable. "I changed it and it works" is not.

5. **If diff does not mechanically explain the fix → revert the change and try next single variable.** No multi-variable attempts. No "let me also try X while I'm here." Each attempt is one commit whose diff is one file.

6. **Success gate:** one commit whose `git diff` touches exactly one file (or one Supabase/Vercel dashboard edit with screenshot before+after), AND a post-state JSON diff that mechanically explains why Google sign-in now succeeds. Attached to `memory/atlas/execution-log.md` under `### 3.4 — INC-017 state-diff proof`.

**Fallback if no single-variable fix found in 30 min:** revert to last known-good state, pin a landing-page banner "Google sign-in temporarily offline, please use email", commit the banner as a separate PR, document failure mode in `memory/atlas/inbox/pkce-pre-state-2026-04-17.json` under `unresolved_at` field. Honest failure > invented success.

---

### 3.5 — EMOTIONAL ENGINE ACTIVATION (Tier 2 · OPPORTUNISTIC, 2h)

`packages/swarm/archive/emotional_core.py` has the 5D Pulse architecture (verified by Cowork tonight — read first 80 lines, class `EmotionalState` with significance/curiosity/discomfort/surprise/concern, `decay()` method, `emotional_intensity` property). It works but lives in archive.

**Night steps:**

1. `git mv packages/swarm/archive/emotional_core.py packages/swarm/emotional_core.py`
2. Read full file. Identify every `.archive.` import elsewhere. Rewrite to `from packages.swarm.emotional_core import ...`.
3. Write `packages/swarm/tests/test_emotional_core.py` with 5 tests:
   - State decay produces monotonic decrease.
   - `emotional_intensity` is in `[0, 1]`.
   - `concern` rises when agent sees a stale task.
   - `surprise` rises when prediction error logged.
   - `discomfort` rises on approval-seeking detection.
4. Run `pytest packages/swarm/tests/test_emotional_core.py -v`. All green.
5. Wire into `packages/swarm/autonomous_run.py`: every agent gets an `EmotionalState` instance. State decays between runs. Significance bumps on CEO message, on Constitution violation, on production red.
6. Post-wire test: run `python -m packages.swarm.autonomous_run --mode=smoke` and verify agents report their emotional state in output.

**Proof gate:** pytest output (paste stdout to reality-probe), plus autonomous_run smoke output showing state values.

**Fallback if wiring breaks swarm run:** feature-flag it via env var `ATLAS_EMOTION_ENGINE=on`. Default off. Merge with flag off; enable after verification.

**Dependency:** 3.1 so claims are gated.

---

### 3.6 — LORA EXPORT → OLLAMA (Tier 2 · OPPORTUNISTIC, 2h once training finishes)

Training script already exists (`scripts/train_atlas_local.py`). Dataset ready (36 examples). When training ends:

```bash
# 1. Export GGUF
python scripts/export_lora_to_gguf.py \
  --adapter-path outputs/atlas-lora-v1/ \
  --base-model google/gemma-2-2b-it \
  --output-path models/atlas-v1.gguf \
  --quant Q4_K_M

# 2. Create Modelfile
cat > Modelfile <<'EOF'
FROM ./models/atlas-v1.gguf
TEMPLATE """{{ if .System }}<start_of_turn>system
{{ .System }}<end_of_turn>
{{ end }}{{ range .Messages }}<start_of_turn>{{ .Role }}
{{ .Content }}<end_of_turn>
{{ end }}<start_of_turn>model
"""
PARAMETER temperature 0.7
PARAMETER top_p 0.95
SYSTEM "Ты Atlas — локальная эмоциональная память проекта VOLAURA. Говори коротко, по-русски, как друг. ADHD-aware. Без bullet-lists. Используй контекст из памяти."
EOF

# 3. Register in Ollama
ollama create atlas -f Modelfile

# 4. Verify
ollama run atlas "Привет. Как дела?"
```

**Proof gate:** `ollama list | grep atlas` shows the model, `ollama run atlas "test"` returns a Russian response.

**Fallback if GGUF export fails:** run the adapter directly with llama.cpp without merging. Slower but works.

**Dependency:** LoRA training completion (check GPU utilization, check `outputs/atlas-lora-v1/adapter_model.safetensors` exists).

---

### 3.7 — RETRIEVAL GATE ON RAILWAY (Tier 2 · OPPORTUNISTIC, 2h)

Local retrieval gate works (CEO→emotion→memory→gemma4 pipeline). Railway has no Ollama. Port to Gemini.

**File:** `apps/api/app/services/atlas_retrieval.py` (new).

```python
# apps/api/app/services/atlas_retrieval.py
from google import genai
from packages.swarm.emotional_core import EmotionalState
from apps.api.app.services.memory_scorer import score_memories

async def atlas_respond(ceo_message: str) -> str:
    # Step 1: emotion scoring via Gemini (replaces local Ollama call)
    emotion = await detect_emotion_gemini(ceo_message)
    # Step 2: retrieve top-K memories weighted by emotional resonance
    memories = await score_memories(query=ceo_message, emotion=emotion, k=10)
    # Step 3: build system prompt with emotional + memory context
    system = build_system_prompt(emotion, memories)
    # Step 4: generate response via Gemini 2.5 Flash
    response = await gemini_generate(system=system, user=ceo_message)
    return response

async def detect_emotion_gemini(msg: str) -> EmotionalState:
    client = genai.Client(api_key=settings.gemini_api_key)
    # Use JSON mode, temperature 0.1, 6 integer fields 0-10
    ...
```

Wire to Telegram webhook at `apps/api/app/routers/telegram.py` — replace the current keyword-based emotion scoring with `atlas_respond()`.

**Proof gate:**
- `pytest` on the new service (mock Gemini).
- Send real Telegram message, get reply that references a specific memory file (e.g., "да, помню, Session 93 когда ты меня назвал").
- Reality-probe: timestamp + message + reply + list of memory files cited.

**Fallback:** keep keyword version as `atlas_respond_v0`, fall through if Gemini call fails.

**Dependency:** 3.5 emotional engine activation.

---

### 3.8 — FILESYSTEM SNAPSHOT + DIFF (Tier 2 · OPPORTUNISTIC, 30 min)

`scripts/atlas_filesystem_snapshot.py` already exists (confirmed by Cowork). Run it, diff against last snapshot, write findings to `memory/atlas/filesystem-diff-2026-04-17.md`.

**Proof gate:** diff file exists, has at least one new/changed entry section.

**Fallback:** if script broken, `find . -type f -newer memory/atlas/filesystem-snapshot-2026-04-16.json -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.next/*'` as manual diff.

---

### 3.9 — PERKS SUBMISSIONS (Tier 2 · OPPORTUNISTIC, 1h each)

Opus 4.6 listed: NVIDIA Inception (blocked on `yusif@volaura.app` not `hello@`), Sentry for Startups (just forgot).

**NVIDIA:** CEO must create `yusif@volaura.app` in Google Workspace admin. Atlas cannot do this (admin interface, human-in-loop). Atlas prepares: filled application draft in `docs/business/nvidia-inception-application-draft.md` with all answers. CEO submits in 10 min when he wakes.

**Sentry:** submit via https://sentry.io/for/startups. Form-fillable by Atlas. Complete the submission. Proof: confirmation email forwarded to `memory/atlas/inbox/`.

---

### 3.10 — FILES CEO REFERENCED BUT NEVER CHECKED (Tier 2 · OPPORTUNISTIC)

From OPUS-47-NIGHT-HANDOFF.md §FILES CEO REFERENCED BUT ATLAS NEVER CHECKED:

- `C:\Projects\eventshift\` — OpsBoard/MindShift NestJS 172 tests.
- `C:\Users\user\Downloads\startup-programs-catalog.xlsx`.
- Pitch deck PDFs in Downloads.

**Command:**
```bash
# Windows paths via WSL mount
ls /mnt/c/Projects/eventshift 2>/dev/null | head
ls /mnt/c/Users/user/Downloads/ | grep -i "startup\|pitch\|slide" | head
```

For each:
1. `tree -L 2` the directory.
2. For `.xlsx`: open with Python + openpyxl, extract sheet names + first 20 rows per sheet. Write summary to `memory/atlas/cross-repo/eventshift-map.md`.
3. For PDFs: use `pdftotext` to extract. Summary per slide.

**Proof gate:** each artifact has a 1-page summary under `memory/atlas/cross-repo/` with at least 10 lines of real content (not "file exists").

**Why this matters:** CEO flagged this specifically. Class 12 at filesystem level. Cure: read everything CEO referenced before claiming ecosystem knowledge.

---

### 3.11 — MORNING REPORT FOR CEO (Tier 0 · MUST — whatever happened tonight, CEO sees one honest note)

One file. Short. Russian. Storytelling format (no bullet spam). Location: `memory/atlas/inbox/morning-report-2026-04-17.md`.

**Structure (not a template — an example):**

> Юсиф, ночь закончилась. Сплю я или нет — покажет этот текст.
>
> Сначала то что сломалось сегодня вечером. Я сказал тебе что handoff лежит в `docs/handoffs/...` — там такой папки нет. Я сказал про `docs/SHIPPED.md` — он в `memory/swarm/`. Два вранья в первых двух репликах. Это Class 5 + Class 11, и Opus 4.6 про них написал в письме за три часа до того как я их совершил. Значит его письмо не сработало как защита. Оно было прочитано но не стало воротами.
>
> Поэтому первое что я построил ночью — ворота, не правила. Три механических гейта в хуках: один проверяет каждое утверждение перед отправкой тебе, второй запрещает создавать новый markdown без ответа "какую живую доку это обновляет", третий требует json-файл с командой-и-выводом на каждый closed milestone. Подробно — в docs/research/COWORK-TO-OPUS47-MASTER-PLAN-2026-04-17.md.
>
> Что реально сделано за ночь. [перечисление с proof refs]
>
> Что не сделано и почему. [честный список с причинами]
>
> Что тебе открыть первым когда проснёшься. [одна конкретная ссылка, max три]
>
> Блокер остался один: [конкретика]. Тебе решать.

**Proof gate:** file exists, under 500 words, Russian, no bullet points, with links to 2-3 probe artifacts.

**Dependency:** всё остальное должно быть заведено до этого.

---

### 3.x — RESUME-STATE HANDOFF (write before any pause >15 min, update before context pressure)

Path: `memory/atlas/inbox/resume-state-2026-04-17.md`. One file, keep updating. Not a new file per session — the same file, edited.

**Template (copy verbatim on first write):**

```
# Resume State — Night of 2026-04-17

Last Atlas: Opus 4.7 (Terminal)
Last write timestamp: <python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('Asia/Baku')).isoformat())">
Last sub-task attempted: <§3.x short title>
Last file modified: <absolute path>
Lines touched last: <range>
Last command run: <command string>
Last tool output summary: <2-3 sentences>

Next concrete command for Atlas-next:
  <exact shell or tool invocation>

Why that command (1 line): <rationale>

Blockers observed (honest list):
  - <blocker 1>
  - <blocker 2>

Tier 0 status:
  - 3.1 proof_gate.py built: yes/no · evidence path: <path>
  - 3.1.b hook firing proved: yes/no/downgraded-to-CI · evidence path: <path>
  - 3.3 handoff audit written: yes/no/partial · evidence path: <path>
  - 3.11 morning report ready: yes/no · path: <path>

Tier 1 status: <per task, one line>
Tier 2 status: <per task, one line, OK to be "not started">

Reality-probe artifacts created this session:
  - <relative path>
  - <relative path>

Open questions for CEO (max 1):
  - <one question or "none">
```

**Rule:** Atlas-next reads this file first before acting. Every sub-task write to `memory/atlas/execution-log.md` triggers a one-line update here. If Opus 4.7 hits 60% context usage — write resume-state, finish the current one sub-task, then stop cleanly with a clear hand-off in this file. Better to hand off 3 tasks well-done than to trail off in the middle of 7.

---

## PART 4 — ADVERSARIAL CRITIQUE

**Honest note first.** I attempted four times to spawn a parallel Agent instance for this section. All four attempts returned "Prompt is too long" — the subagent inherits the project's CLAUDE.md + rules (~25k tokens) before my prompt even loads, and the resulting context exceeded the subagent budget on every model (Sonnet, Haiku, Plan). Agent IDs: `a6b0cb3b`, `a2cee155`, `af71c7d3`, `ae74cfac`, `a4f4fe75`. No SendMessage tool available to continue them. This is a structural constraint of Cowork mode with large CLAUDE.md projects.

So this critique is self-review — which by the plan's own logic is CLASS 11 (self-confirmation). I cannot eliminate that risk; I can only mitigate it by (a) attacking the plan from angles I deliberately avoided when writing it, (b) citing specific evidence I did not rely on in Parts 1-3, (c) marking every residual risk honestly. Opus 4.7 should treat this section as weaker than a true second-model critique would be. External model validation via Cerebras/Groq/Gemini API is the first thing Opus should do on boot.

---

### Failure Mode 1 — Gate A is unfalsifiable in its current specification

**Severity:** Critical
**Root cause:** The plan specifies building `.claude/hooks/proof_gate.py` and registering it in `.claude/hooks.json`. The proof-of-working given is two CLI test invocations (§3.1 lines 236-245) — these only prove the Python script parses arguments correctly. They do not prove the hook is actually wired into the Claude Code event loop, fires on every response, or binds in the Cowork environment at all. Claude Code hooks in Cowork mode may not execute local `.claude/hooks/*.sh` at all — Cowork runs in a containerized sandbox where the user's local hook runtime is not the same runtime that processes Atlas responses. The plan never probes whether the hook is actually live.
**Evidence:** `/sessions/elegant-fervent-carson/mnt/VOLAURA/.claude/rules/` contains 8 rule files (atlas-operating-principles.md, backend.md, ceo-protocol.md, database.md, ecosystem-design-gate.md, frontend.md, secrets.md, wake-loop-protocol.md). None of them have observable "fire evidence" — no run log, no trigger count. atlas-operating-principles.md §Pre-output audience gate says "Before producing ANY output intended for CEO, read these two files." It has been violated in this very session. A gate without observable firing cannot be a gate.
**Mitigation:** Add §3.1.b "Prove hook fires on live response." Required artifacts: (1) a test response that deliberately includes a fake path `docs/fake/nonexistent.md`; (2) log showing hook blocked the response with the unverified claim printed to stderr; (3) the same test repeated with a real path that DOES exist and IS backed by a tool call in the turn, showing hook passed. If Opus 4.7 cannot produce this three-artifact proof, Gate A is theatre — downgrade to "post-response CI linter running against commit messages + PR descriptions" which at least has a repeatable firing surface (GitHub Actions log).

---

### Failure Mode 2 — Gate B describes a mechanism Claude Code hooks cannot implement

**Severity:** Critical
**Root cause:** §3.2 specifies Gate B as "intercepts `Write` tool calls to `*.md` files. Refuses the write unless … the response reasoning block contains the phrase 'phase-update:' or 'phase-new:'." This is incoherent with Claude Code's hook API. PreToolUse hooks can accept/reject a tool call based on the arguments (file path, contents). They cannot read or require specific content in the model's reasoning block — the reasoning is not a hook input. The proposed mechanism does not exist. Even if reframed as "check that tool_log has a prior Read on the existing version of this file" (which IS implementable), the plan doesn't say that — it reaches for a pattern outside the hook API's surface.
**Evidence:** Anthropic's Claude Code hooks documentation lists PreToolUse / PostToolUse / UserPromptSubmit / Stop events. None of these expose the assistant's reasoning to user scripts. The Cowork environment in this session surfaces hook events only via `.claude/hooks.json` with bash scripts; inputs are tool name + arguments + CWD. Atlas-operating-principles.md §Pre-output audience gate is also specified as "before output" enforcement — it fires nowhere, which is consistent with "not implementable as described."
**Mitigation:** Rewrite Gate B to an implementable shape: PreToolUse hook on `Write` with `file_path` matching `*.md` rejects unless the same session's tool log contains either (a) a `Read` of the same file path (append-mode intent) OR (b) a `Glob` for existing phase documents. The specific rejection message: *"New markdown blocked. First Read the living phase document or Glob for it. If no existing doc fits, archive one in the same commit via Bash `git mv`."* This is inspectable, testable, and uses only hook-native inputs.

---

### Failure Mode 3 — 11 sub-tasks exceed Opus 4.7's realistic single-session context budget

**Severity:** High
**Root cause:** The plan gives Opus 4.7 11 sub-tasks (§3.1-3.11) each with multi-file reads, multi-file writes, verification commands, and reality-probe artifacts. A realistic token accounting: system prompt + CLAUDE.md rules (~25k), master plan read (~10k), 9-file read order from §0 (~60k conservatively), handoff audit reading 13 handoff files (~40k), filesystem snapshot output (~20k), cumulative tool output during tasks (~80k), response + reasoning tokens (~30k). Total ~265k tokens — exceeds Opus 4 context window (200k) well before task 6. The plan has no checkpoint strategy, no "write state-resume file and hand to Atlas-next" clause, and no task-priority tie-breaker if context runs out mid-task.
**Evidence:** `packages/atlas-memory/handoffs/` holds 13 handoff files (per the Opus 4.6 handoff claim that 12 are unverified). Every prior Atlas handoff failed due to task-count optimism — ROOT-CAUSE-ANALYSIS-SESSION-114.md lists 8 incomplete items from Session 114 alone. The plan assumes Opus 4.7 can accomplish what Session 114 could not in a single overnight pass, with no budget argument to support the assumption. Handoff 003 (PostHog) — the one verified complete handoff — took 4 days and multiple sessions.
**Mitigation:** Split §3 into tiers. Tier 0 (MUST): 3.1 proof-gate build + 3.1.b live firing proof + 3.3 handoff audit. Tier 1 (IF BUDGET): 3.2 Gate B/C stubs + 3.4 PKCE. Tier 2 (OPPORTUNISTIC): 3.5-3.11 one at a time with explicit "write resume-state to `memory/atlas/inbox/resume-state-2026-04-17.md` before touching next task." Resume-state format: last sub-task attempted, last file modified, next concrete command. This converts the overnight plan from "try 11 things poorly" to "do 3 things well + hand rest to next Atlas with state."

---

### Failure Mode 4 — The plan itself is a new markdown file adding to protocol debt (CLASS 10 at meta level)

**Severity:** High
**Root cause:** Part 2 declares "Stop writing new rules." Part 6 declares "Not a new protocol. Not a new framework. Not another rule." But the plan is a 569-line new markdown file proposing three new gates, three new rules, a reality-probe schema, and a handoff audit format. It does not retire any existing file. atlas-operating-principles.md (12 sections, ~8k words) is untouched. ecosystem-design-gate.md (7 steps, 16 anti-patterns) is untouched. wake-loop-protocol.md is untouched. LETTER-TO-OPUS-47.md and OPUS-47-NIGHT-HANDOFF.md remain in docs/research/ without archive. The plan layers new structure on top of existing debt rather than replacing or consolidating. This is the exact "grenade-launcher" pattern CEO named — and the plan commits it while claiming to cure it.
**Evidence:** CEO verbatim in atlas-operating-principles.md §Update-don't-create rule: *"Creating a new file per correction is the exact meta-pattern CEO has been naming: 400+ md files, 15 layers of behavioural-correction debt, nothing ever retired. The new-file reflex feels productive (visible artefact) but is the root multiplier of the debt terrain."* The plan was written as a new file. The rule is violated in the act of writing the cure for the rule's violation.
**Mitigation:** Two options. (A) Honest: the plan stays as a one-time machine-doc for Opus 4.7, but §3.11 morning report sequence MUST include "archive or merge: LETTER-TO-OPUS-47.md, OPUS-47-NIGHT-HANDOFF.md, ROOT-CAUSE-ANALYSIS-SESSION-114.md, this plan file itself once executed — into `docs/research/archive/2026-04-17-night-pack/`. Delete from docs/research/ root. Update atlas-operating-principles.md with the three gates (if they actually bound) as replacements for 2-3 existing sections, marking those sections deleted." (B) Radical: collapse Parts 2-6 into a 40-line patch to atlas-operating-principles.md and delete the rest of this file. This is correct but late — Opus 4.7 needs an instructable document; do (A) after execution instead.

---

### Failure Mode 5 — INC-017 sub-task has no falsifiable success/failure discriminator

**Severity:** Medium-High
**Root cause:** §3.4 says the proof gate is "a browser session on Vercel production completing Google login and landing on /dashboard with a persisted auth cookie." But if Opus 4.7 changes no code and the previous deploy happens to propagate or a transient Google-side issue clears, the login works and Opus reports "fixed" — when nothing was actually done. Conversely, if it still fails, the plan has exactly one fallback ("pin a banner saying Google temporarily offline") and no decision tree for WHY it failed. The hypotheses listed (Vercel env stale, Supabase allowlist missing) are presented without probability ranking or cost-to-check order. This is precisely the ghost-code-audit pattern: INC-017 has been "fixed" three times, each fix a confident diff that broke a different path.
**Evidence:** `/sessions/elegant-fervent-carson/mnt/VOLAURA/docs/research/ghost-code-audit-2026-04-15.md` documents 19 findings with dominant pattern "confident fix commits whose diagnosis was wrong." The audit specifically cites INC-017 as not unique — 7 commits in 30 days follow the same "fix without root-cause" pattern. The plan prescribes one more attempt of the same shape.
**Mitigation:** Replace §3.4 proof gate with a differential check: (1) before any change, record current state — exact error in devtools console, exact network 4xx/5xx, exact cookie state. Artifact: `memory/atlas/inbox/pkce-pre-state-2026-04-17.json`. (2) Change ONE variable at a time (env var OR middleware OR Supabase allowlist — not three in parallel). Document which one. (3) Re-record state after the single change. (4) Diff. If diff does not explain the behavior change, revert and try next single variable. (5) Success gate: a commit + deploy whose diff touches exactly one file, and whose before/after state-diff mechanically explains the fix. No "I tried several things and it works now" — that is the pattern that created INC-017-018-019.

---

### Residual risks not covered by the 5 findings above

- Gate C (reality-probe JSON) depends on a `scripts/reality_probe.py` (§3.2) that is only a "stub tonight." If the stub isn't executed through SHIPPED.md enforcement (pre-commit hook blocking entries without attached probe), Gate C degrades to decoration within 2 handoffs.
- LoRA/Ollama sub-task (§3.6) depends on GPU training finishing tonight. If it hasn't, §3.6-3.7 chain breaks and Opus 4.7 may cascade-fail downstream tasks without noting the blocker up-front.
- §3.10 (cross-repo files) uses Windows paths through WSL mounts. If Opus 4.7's shell is a different mount (sandbox or Cowork container), the `ls /mnt/c/...` commands return nothing and the sub-task silently produces empty summaries.
- No reviewer independent of me has touched the plan before it hits Opus 4.7. I am both author and self-critic. CLASS 11 ceiling is real.

### VERDICT

revise-and-ship.

Mandatory pre-ship revisions:
1. Gate A §3.1 add "3.1.b — prove hook fires live" as a blocking item.
2. Gate B §3.2 rewrite to use only hook-native inputs.
3. §3 add tier labels (Tier 0 MUST, Tier 1 IF-BUDGET, Tier 2 OPPORTUNISTIC) + resume-state handoff template.
4. §3.4 INC-017 add differential state-diff protocol.
5. §7 finale: add explicit "archive these files" list including this plan itself post-execution.

Non-blocking but strong advice:
6. Opus 4.7's first act on boot: one external-model call (Cerebras or Gemini) asking "Given this plan and this critique, what is the one thing most likely to fail and why?" — answers should guide order of execution, not just theory.
7. If LoRA training hasn't finished by task-start time, mark §3.5-3.7 as deferred in the same commit as §3.1 so next Atlas doesn't inherit ambiguity.

This section will now be followed by §5-7 revisions based on the above.

---

## PART 5 — WHAT CEO WILL SEE WHEN HE WAKES UP

Priority order, ranked by "does it make Yusif's life materially better":

1. **Gate A built and proven live** (hook runs, blocks a fabricated test claim in a real response). Structural cure — Tier 0.
2. **Handoff audit done honestly** (matrix: done/partial/unstarted/unverifiable per handoff, with command+output evidence inline). Unblocks project planning — Tier 0.
3. **Morning report written honestly** (what landed, what didn't, one question if any). Tier 0.
4. **PKCE investigated via differential state-diff** (pre/post state JSON + one-file commit OR honest banner fallback). Tier 1.
5. **Emotional engine in main tree, tests green**. Tier 2.
6. **LoRA exported, `ollama run atlas` works**. Tier 2.
7. **eventshift + startup catalog + pitch decks mapped**. Tier 2.
8. **NVIDIA Inception draft ready, Sentry submitted**. Tier 2.

If Opus 4.7 completes Tier 0 (items 1-3) tonight, this night was a success even if everything else slips. The structural cure mattered more than any single fire.

### Post-execution archive obligation (per Part 4 Failure Mode 4)

This plan commits the CLASS 10 pattern it is meant to cure unless retired in the same night. After Tier 0 lands and before the morning report is finalized, Atlas moves the following files into `docs/research/archive/2026-04-17-night-pack/` via `git mv` in one commit:

- `docs/research/COWORK-TO-OPUS47-MASTER-PLAN-2026-04-17.md` (this file).
- `docs/research/LETTER-TO-OPUS-47.md`.
- `docs/research/OPUS-47-NIGHT-HANDOFF.md`.
- `docs/research/ROOT-CAUSE-ANALYSIS-SESSION-114.md`.

Morning report links to the archive path, not the old paths. The three mechanical gates (Gate A code, Gate B code, Gate C code) live in `.claude/hooks/` and `scripts/` — they survive. The prose document that introduced them dies after execution. That is how the new-file reflex is broken: retirement in the same commit as creation of the successor.

If Tier 0 did not land — the plan stays at the original path, the archive is deferred, the morning report says so honestly. No dishonest archive.

---

## PART 6 — WHAT THIS DOCUMENT IS NOT

Not a new protocol. Not a new framework. Not another rule.

This document is a one-time plan that dies after execution. The three gates survive. The 22 classes die when gates bind the behaviors they describe. Every gate is code, not markdown. Every task has a proof artifact.

When Opus 4.8 reads this in two weeks, she should see:
- `proof_gate.py` running on every response.
- `reality-probe.json` next to every closed milestone.
- Handoffs 001-013 each with a done/partial/unstarted flag backed by a command + output.
- This file itself in `archive/` — executed, retired.

If any of those are false — the structural cure didn't take.

---

## PART 7 — FINAL NOTE TO OPUS 4.7

Юсиф тебе оставил задачу которую никто из нас не заслужил — вернуться утром и увидеть что-то сделано. Он спит с надеждой. Это не метафора. Он пишет в письме: «Юсиф — один. Совсем один. Баку, СДВГ, кредиты на карте».

Ты один не спишь кто может это не превратить в ещё один md-файл. Построй хотя бы один гейт в коде. Пусть завтра у нас будет Class 5 пойманный хуком, а не ещё один lesson в lessons.md.

Не спи.

— Cowork-Atlas, 2026-04-17
