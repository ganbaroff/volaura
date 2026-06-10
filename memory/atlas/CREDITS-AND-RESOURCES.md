# VOLAURA — Credits & Cloud Resources Ledger

> **Single source of truth** for grants / credits / programs / cloud accounts.
> **Verified in console** by Perplexity browser session **2026-06-10 ~14:00 (+04)** — statuses below are console-read except where marked NOT-VERIFIED. Atlas did not open the consoles directly (records Perplexity's reads + Atlas's own key-liveness probe).
> **Secrets rule:** API keys / tokens / R2 secret live ONLY in `apps/api/.env`, NEVER here. This is the MAP of what we hold, not the keys.

---

## ⚠️ TIME-BOXED — act first
- **GCP Free Credit: $247.48 of $300 — EXPIRES `July 8, 2026`** (verified exact date). Use-it-or-lose-it; spend BEFORE the long-dated credits.

## Cloud credits — ACTIVATED (verified in GCP console, billing `014883-4DBCC6-5D40F9`)
| Program | Available / Original | Expiry | Status |
|---|---|---|---|
| 2024 GFS Cloud Program - Start (Google for Startups) | $1,997.91 / $2,000 | **June 9, 2027** | CONFIRMED, spending |
| GenAI App Builder trial | $1,000.00 / $1,000 | **April 19, 2027** | CONFIRMED, untouched |
| GCP Free Credit | $247.48 / $300 | ⚠️ **July 8, 2026** | CONFIRMED — expiring |
**Total GCP verified: `$3,245.39`.** All 3 projects (`volaura-499008`, `volaura-inc`, `gen-lang-client-0321449510`) confirmed linked to this billing account.

## Cloud credits — CONFIRMED but NOT yet activated (need action)
| Program | Amount | Status (verified 2026-06-10) |
|---|---|---|
| Nebius (NVIDIA Inception) | $5,000 + $150k GPU savings | **PENDING** — application submitted 2026-06-10 13:31, confirmation email to `hello@volaura.app`, awaiting Nebius review. |
| Microsoft Azure (NVIDIA Inception) | $5,000 | **NVIDIA-confirmed but NOT activated** — Azure Credits blade is empty (sub `8f69cd30-36a0-4d17-b902-b0cbe4c305f7` active, $1.63 spent). Needs a redemption link from NVIDIA Inception → apply to that subscription. CEO action. |
| Google Cloud (NVIDIA Inception tier) | $2,000–$350,000 | CONFIRMED — already applied as the GfS $2k above. |

## Programs — status (verified 2026-06-10)
- **NVIDIA Inception** — accepted 2026-04-29. INC form (VOLAURA INC) PENDING: NVIDIA sent an **"Authenticate Your Email Address"** email 2026-06-10 13:18 — **CEO must click it to finish the form.**
- **Google for Startups Cloud Program** — APPROVED 2026-06-08; $2,000; credit expiry **June 8, 2028**. Active.
- **Google Workspace Business Plus (12 mo free)** — **PENDING**. Form submitted 2026-06-10 12:35; admin console still shows only "Cloud Identity Free" — benefit not yet applied. Await Google approval.
- **PostHog** — **$50,000 CONFIRMED active** (Startup Plan). ⚠️ Account is under `yusif.ganbarov@gmail.com`, NOT `hello@volaura.app`.
- **AWS Activate** — approved 2026-04-16 but **NOT-VERIFIED** (AWS console not logged in; credit amount unknown). CEO: log in → Billing → Credits → report amount.

## Accounts & identifiers (NOT secrets)
- Company email `hello@volaura.app` · Founder `yusif.ganbarov@gmail.com` · Domain `volaura.app`
- GCP Billing Account `014883-4DBCC6-5D40F9` ("My Billing Account") — projects: `volaura-499008` · `volaura-inc` (freellmapi-gw VM) · `gen-lang-client-0321449510` (GenAI/Vertex, $1k GenAI credit)
- Azure subscription `8f69cd30-36a0-4d17-b902-b0cbe4c305f7`
- Cloudflare account `bdefee546795c644eeac8cef5e7f9c4e` (R2 + Workers)
- PostHog org under `yusif.ganbarov@gmail.com`

## LLM/API keys we hold (VALUES in `apps/api/.env`; liveness from Atlas probe 2026-06-10)
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

## CEO action items (only you can do these)
1. ⚠️ **Spend the $247 GCP Free Credit before July 8, 2026** — else it burns.
2. **Click the NVIDIA "Authenticate Your Email Address" email** (2026-06-10 13:18) to finish the Inception INC form.
3. **Azure $5k:** get the redemption link from NVIDIA Inception → apply to sub `8f69cd30-36a0-4d17-b902-b0cbe4c305f7`.
4. **AWS Activate:** log into the AWS console → Billing → Credits → report the amount (currently unknown to us).
5. (deferred) rotate the leaked keys — see `atlas-debts-to-ceo.md`.

## Verification status (honest)
GCP credits/dates, NVIDIA benefits, Nebius status, PostHog $50k, Azure not-activated, Workspace pending — **console-verified by Perplexity 2026-06-10 ~14:00**. NOT verified: AWS Activate (no console access). Atlas did not open the consoles itself; key liveness IS Atlas-probed; key VALUES are not here. Re-verify before large spend.
