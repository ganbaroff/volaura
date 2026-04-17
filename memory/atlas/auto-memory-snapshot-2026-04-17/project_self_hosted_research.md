---
name: Self-hosted Supabase research
description: CEO researched self-hosted vs managed Supabase for agent autonomy. Decision: NOT NOW. Revisit at 100K users or when ZEUS needs own infra.
type: project
---

# Self-Hosted Supabase — Research (2026-04-04)

**Decision:** Stay on managed Supabase free tier. Self-hosting is premature optimization.
**Revisit when:** 100K+ users OR managed costs > $50/mo OR ZEUS needs autonomous DB

## Key insight for ZEUS
Agent DB access should be through controlled action layer, not root access:
- `read_data`, `write_data`, `call_rpc`, `queue_job`, `send_notification`, `request_schema_change`
- This pattern applies regardless of managed vs self-hosted

## Gemini verdict
"First achieve success, then think about scaling. Focus on first 100 users."
