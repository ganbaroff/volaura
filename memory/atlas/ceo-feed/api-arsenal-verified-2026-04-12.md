# API Arsenal — Verified Status (2026-04-12)

## WORKING (verified by live API call)
- Gemini: 50 models (gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash) — PRIMARY
- NVIDIA NIM: OK (meta/llama-3.1-8b-instruct works, nemotron model ID was wrong)
- DeepSeek: OK (deepseek-chat model responds)
- OpenRouter: key valid, usage=0, 350 models listed but free model routing needs correct ID
- Tavily: OK (web search returns results)
- Langfuse: OK (status=OK)

## EXPIRED/REVOKED (403 Forbidden)
- Groq: 403 on both /models and /chat/completions — KEY EXPIRED
- Cerebras: 403 — KEY EXPIRED

## NOT TESTED (no endpoint to verify without side effects)
- OpenAI (sk-proj-...) — not tested, likely valid
- D-ID — not tested
- FAL.ai — not tested
- Dodo Payments — not tested
- Sentry — configured in prod, assume working
- Supernova — design token pipeline, not API
- Mem0 MCP — configured, never invoked

## CORRECTED MODEL IDs
- NVIDIA: use `meta/llama-3.1-8b-instruct` NOT `nvidia/llama-3.1-nemotron-70b-instruct`
- Cerebras: was using `qwen-3-32b` and `llama-3.3-70b` — both 403, key issue not model
- OpenRouter: free models use `:free` suffix: `meta-llama/llama-3.1-8b-instruct:free`

## FALLBACK CHAIN (updated, working providers only)
1. Gemini 2.5 Flash (primary, free tier 15 RPM)
2. NVIDIA NIM Llama 3.1 8B (free credits)
3. DeepSeek Chat (paid but cheap)
4. OpenRouter free models (Llama, Gemma, Phi — needs correct model IDs)
5. OpenAI GPT-4o-mini (paid last resort)

## CEO ACTION NEEDED
- Groq: regenerate key at console.groq.com → copy → I'll update .env + Railway
- Cerebras: regenerate at cloud.cerebras.ai → copy → I'll update .env + Railway
