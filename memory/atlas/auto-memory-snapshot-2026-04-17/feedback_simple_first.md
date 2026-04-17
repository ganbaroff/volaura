---
name: Simple Steps First
description: Always exhaust simple solutions before complex ones. CEO directive after CTO repeatedly chose complex debugging over simple replacement.
type: feedback
---

# Simple Steps First — Never Debug What You Can Replace

Always use simple steps first, then escalate to complex approaches.

## Why

CTO pattern of choosing complex debugging over simple replacement wasted hours repeatedly:
- **OAuth**: 10-minute replacement took 2+ hours of debugging
- **Vercel**: Could have used regular path, chose manifest debugging instead
- **Microphone**: Attempted Python debugging instead of hardware toggle first

This is inefficiency disguised as thoroughness. Simple is faster AND more reliable.

## How to Apply

**Before any fix:** Is there a simpler replacement that avoids debugging entirely?
- Replace > Repair
- Hardware before software
- Environment before code
- Restart > Debug
- Update > Investigate

**Before debugging >5 minutes:** Ask "Did I create this problem?"
- If yes → replace the thing you created, don't debug it
- If no → is there a working alternative I can swap in while investigating root cause?

**Hardware before software:**
- Connection issues? Check cable/WiFi before code
- Audio problems? Toggle hardware mute before Python
- Build failures? Clear cache before refactoring

**When launching agents:** Use DIVERSE models
- Never 7 identical haiku evaluators
- Rotate: NVIDIA, Groq, Gemini, local Qwen3, Claude
- Different models catch different blind spots

**Integration fixes (webhook, API, env var, OAuth):**
- **READ config on BOTH sides FIRST** → match them → done
- Never change config before understanding what both sides currently have
- Mistake #82: Telegram webhook 403. Railway had secret X. CTO generated new secret instead of reading X. 3 redeploys, 10 min wasted. Fix was 1 API call.
- Rule: `railway variables list | grep KEY` → read value → use THAT value in registration → done
