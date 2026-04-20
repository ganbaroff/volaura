---
description: Verify work end-to-end, run simplify, open a PR. Boris Cherny's full verification workflow for completed features.
---

When this command is invoked, execute these steps in order and STOP on any failure:

**Step 1 — End-to-end verification** (choose verifier for the task type):
- Backend: run the service, hit the changed endpoint, confirm expected response
- Frontend: preview_snapshot + preview_console_logs — zero errors required
- Full stack: `cd apps/web && npx tsc -b --noEmit && cd ../api && python -m pytest -q`

If verification fails: STOP. Report the failure with the exact error. Do NOT proceed to Step 2.

**Step 2 — Simplify**
Invoke the `simplify` skill: review changed code for reuse, quality, and efficiency. Fix any issues found before opening PR.

**Step 3 — Open PR**
```bash
gh pr create --title "<concise title>" --body "$(cat <<'EOF'
## Summary
<what was done>

## Verified
<how it was tested>

🤖 Generated with Claude Code /go
EOF
)"
```

This is the `/go` skill pattern from Boris Cherny tip #6.
