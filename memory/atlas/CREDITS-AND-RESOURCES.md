# VOLAURA — Credits & Cloud Resources Ledger

> **Single source of truth** for grants / credits / programs / cloud accounts.
> **Source:** CEO + Perplexity browser session, 2026-06-10. **NOT independently verified by Atlas** (no dashboard access) — reported balances/statuses; re-check the console before relying on a number.
> **Secrets rule:** API keys / tokens / R2 secret live ONLY in `apps/api/.env`, NEVER here. This is the MAP of what we hold, not the keys.

---

## ⚠️ TIME-BOXED — act first
- **GCP Free Credit: $247.48 of $300 — EXPIRING ≈28 days from 2026-06-10** (≈ early July 2026). Use-it-or-lose-it; spend before the non-expiring credits.

## Cloud credits — ACTIVATED (GCP billing `014883-4DBCC6-5D40F9`)
| Program | Available | Original | Status |
|---|---|---|---|
| 2024 GFS Cloud Program - Start (Google for Startups) | $1,997.91 | $2,000 | Available, spent $2.09. Approved 2026-06-08 via `hello@volaura.app`. |
| GenAI App Builder trial | $1,000.00 | $1,000 | Available (Vertex/Gemini project) |
| GCP Free Credit | $247.48 | $300 | ⚠️ EXPIRING ≈28d |
**Total GCP available now: ~$3,245.**

## Cloud credits — CONFIRMED, NOT activated (need partner action)
| Program | Amount | Status |
|---|---|---|
| Nebius (NVIDIA Inception) | $5,000 + $150k GPU savings | NVIDIA-Confirmed; application SUBMITTED 2026-06-10 → $5k on activation, up to $100k reserved discounts. Await reply. |
| Microsoft Azure (NVIDIA Inception) | $5,000 | NVIDIA-Confirmed; needs direct partner activation. |
| Google Cloud (NVIDIA Inception tier) | $2,000–$350,000 | NVIDIA-Confirmed (the $2k GfS likely this tier). |

## Programs — status
- NVIDIA Inception — accepted 2026-04-29. INC form (VOLAURA INC) ~95% filled; PENDING: LinkedIn URL + Submit (CEO).
- AWS Activate — approved 2026-04-16 (credit amount TBD — confirm in console).
- Google for Startups Cloud Program — approved 2026-06-08 (= the $2k GfS).
- Google Workspace Business Plus — 12 months free, APPLIED 2026-06-10 (billing `014883-4DBCC6-5D40F9`, domain `volaura.app`, 3 users), pending review.
- PostHog — ~$50,000 credits (CEO-reported; activation TBD — confirm).

## Accounts & identifiers (NOT secrets)
- Company email `hello@volaura.app` (Google for Startups credits land here) · Founder `yusif.ganbarov@gmail.com` · Domain `volaura.app`
- GCP Billing Account `014883-4DBCC6-5D40F9` ("My Billing Account")
- GCP projects: `volaura-499008` (Volaura) · `volaura-inc` (VOLAURA INC — `freellmapi-gw` VM here) · `gen-lang-client-0321449510` (GenAI/Vertex, has $1k GenAI credit)
- Cloudflare account `bdefee546795c644eeac8cef5e7f9c4e` (R2 + Workers)

## LLM/API keys we hold (VALUES in `apps/api/.env`; liveness from 2026-06-10 probe)
| Provider | Liveness | Note |
|---|---|---|
| Groq | WORKING (200) | keep |
| Gemini | alive, quota-limited (429) | use GenAI project |
| Cerebras | key alive (404 model), REMOVED from code by ADR-013 spend policy | keep removed |
| NVIDIA | DEAD KEY (401) | rotate or drop; it's the brain's 1st hop (#131) |
| Azure OpenAI | unverified (404 endpoint) | needs correct deployment |
| Mistral / HuggingFace / Cloudflare(token+R2) | pasted 2026-06-10, not in .env, untested | rotation deferred — see `atlas-debts-to-ceo.md` |

## $0 runtime already running
- freellmapi gateway — $0 LLM proxy, LIVE on GCP `volaura-inc` (`freellmapi-gw`, e2-micro, `http://34.60.182.57:8799`, `/ping` 200 on 2026-06-10). Consolidation target for routing.

## How to USE the credits (the gap CEO hit)
1. GCP credits auto-apply to anything billed to `014883-4DBCC6-5D40F9` — point working projects there.
2. Vertex/Gemini → project `gen-lang-client-0321449510` ($1k GenAI credit).
3. Spend the expiring $247 GCP Free Credit FIRST.
4. Nebius/Azure $5k each → await partner activation emails, then wire.

## Verification status (honest)
All balances/statuses are CEO/Perplexity-reported 2026-06-10, NOT Atlas-confirmed (no console access). Working map; re-verify in each dashboard before spend decisions. Key liveness IS Atlas-probed; key VALUES are not here.
