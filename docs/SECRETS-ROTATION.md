# Secrets Rotation Schedule — v0 stub

**Status:** Stub. Referenced by `docs/VACATION-MODE-SPEC.md` V-MODE 1 ("rotate API keys on the pre-defined rotation schedule in `docs/SECRETS-ROTATION.md`"). Full policy lives in a next sprint after CEO signs off on cadence and tooling.

**Why this file exists today:** so Vacation Mode's "MAY autonomously rotate keys" clause is not a dangling reference. With only the stub, the autonomous rotation right is effectively empty (no key listed ⇒ nothing to rotate). That is the safe default.

---

## Current state

No autonomous rotation is authorized. Every key in `apps/api/.env` and Railway is rotated manually by the CEO on an ad-hoc basis.

## What the full file will specify (next sprint)

- Inventory of all external credentials (OpenAI, Gemini, Groq, NVIDIA, Supabase service, Stripe, Resend, etc.) with their source of truth (Railway / GitHub secrets / .env only).
- Per-key rotation cadence (e.g. 90 days, 180 days, on-suspicion).
- Per-key rotation playbook: where to generate the new value, which env vars to update on Railway, which dependent services need a restart, how to verify the new key works.
- Which keys are eligible for autonomous rotation during Vacation Mode (narrow subset — only keys with a tested, one-step rotation path, zero downtime, and a verification probe).
- Reversibility: every rotation must support rollback to the previous key for at least 24h.

## Until this file is written

Atlas MUST NOT rotate any key autonomously. Any expiring or compromised key is a D-0xx entry in `memory/swarm/proposals.json` with tag `after-vacation`, paging the CEO only if it hits the V-MODE 2 emergency-ping criteria (security incident signal).

## Related files

- `docs/VACATION-MODE-SPEC.md` V-MODE 1 — references this file
- `apps/api/.env` — current source of truth for local creds (gitignored)
- Railway dashboard — production env vars, not in git
- `.env.md` — documentation of which key goes where (in git, sanitized)
