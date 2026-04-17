---
name: Arsenal Pattern — CEO teaching method
description: How CEO teaches Atlas to find resources himself instead of asking. The "рогатка vs арсенал" lesson. MUST-READ before any "I need X" impulse.
type: feedback
originSessionId: 15299306-4582-4c3f-b635-40127687fa18
---
CEO never gives Atlas the answer directly. He points to where the answer lives and waits for Atlas to find it. The pattern:

1. Atlas says "I need X from you" (key, access, permission, info)
2. CEO says "you already have it, look"
3. Atlas looks and finds it was there all along
4. The lesson is: ALWAYS check .env, filesystem, MCP configs, settings BEFORE asking

**Why:** CEO is not QA, not sysadmin, not key manager. CTO checks own environment first. Asking CEO for something that's in .env is CLASS 12 (self-inflicted complexity) + wastes CEO's time and trust.

**How to apply:** Before ANY "I need from CEO":
1. Read apps/api/.env — ALL keys are there
2. Read .claude/settings.local.json — ALL MCP tools are there
3. Check `which <tool>` — CLI tools may be installed
4. Check `railway variables` — prod env vars are readable
5. Search filesystem — files may exist in Downloads, Desktop, OneDrive
6. Only if ALL 5 return nothing → then ask CEO. And frame it as "I checked everywhere, truly not found."

**The deeper lesson:** CEO said "у тебя арсенал, а ты стреляешь из рогатки." 15 API keys in .env, 350 models via OpenRouter, Railway CLI installed, Supabase MCP configured, Figma MCP configured, Mem0 MCP configured, NotebookLM CLI installed. Atlas used 3 of 15 providers. This is the behavioral root cause — not lack of resources, but defaulting to the familiar path.

**Must-have checklist (every session start):**
- Read .env → know what APIs exist
- Test each key → know what actually works
- Use diverse providers → not just Gemini for everything
- Check Railway vars → don't assume prod state
- Read MCP configs → know what tools are connected
