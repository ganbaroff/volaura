# Note to CEO — pending decisions

## Pending action items requiring CEO input

### 1. ANTHROPIC_API_KEY (BLOCKING for Cowork red-team critique)

`scripts/critique.py` infrastructure is built and ready (Anthropic-only wrapper for Cowork-Atlas sandbox to spawn independent persona critiques on `docs/research/az-capital-crisis-2026/`). Cannot test or use without `ANTHROPIC_API_KEY` in `apps/api/.env`.

**Action you need to take:** Either
- **(A) Paste your Anthropic API key in chat.** I save it to `apps/api/.env` as `ANTHROPIC_API_KEY=sk-ant-...` per `.claude/rules/secrets.md`, mirror to GitHub Secrets via `gh secret set`, and we run the first critique batch immediately. Cost ceiling already in script: $3/batch hard abort.
- **(B) If no key yet:** `console.anthropic.com` → API Keys → Create Key → scope "Read + Write". 30 seconds. Paste here.

Without this, Cowork-Atlas remains blocked from independent critique — only self red-team possible (which is not adversarial enough).

### 2. Cowork sandbox network allowlist expansion (LOW URGENCY)

Cowork sandbox can only reach `api.anthropic.com`. Other top-model endpoints (openrouter.ai, api.openai.com, api.deepseek.com, generativelanguage.googleapis.com, api.groq.com, api.cerebras.ai, integrate.api.nvidia.com) all return 403.

**For multi-provider independent critique** (Claude + GPT-5 + Gemini + DeepSeek voices on the same target), Cowork needs network allowlist expansion. The cheapest path: add `openrouter.ai` (single gateway = access to all major models with one API key).

**Action you need to take:** Open ticket with Anthropic platform support — "Cowork app: please extend network allowlist for outbound HTTPS to include openrouter.ai for adversarial multi-provider critique workflow." Without this expansion, all critique remains Claude-family only (Opus/Sonnet via Anthropic API).

This is NOT urgent — Claude-family critique alone already gives independent voices via fresh persona contexts. But for true cross-provider adversarial coverage, this expansion is needed.

---

## Current Cowork-blocking incidents

See `memory/atlas/incidents.md` INC-XXX entry for full details.
