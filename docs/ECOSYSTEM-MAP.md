# ECOSYSTEM MAP — 5-Product Architecture

## Products

| Product | Stack | Status | URL |
|---|---|---|---|
| **VOLAURA** | Next.js 14 + FastAPI + Supabase | Live | volaura.app |
| **MindShift** | Next.js + Capacitor (iOS/Android) + Supabase | Live | mindshift.app |
| **Life Simulator** | Godot 4 | Dev | — |
| **BrandedBy** | FastAPI + fal.ai (MuseTalk) | Dev | brandedby.xyz |
| **ZEUS** | Python swarm + ngrok | Local | localhost |

## Shared Infrastructure

- **Supabase project:** `dwdgzfusjsobnixgyzjk` — shared auth for VOLAURA + cross-product bridge
- **MindShift Supabase:** `awfoqycoltvhamtrsvxk` — separate project, bridged via edge function

## Data Flows

```
MindShift user
  → volaura-bridge-proxy (Supabase edge function, awfoqycoltvhamtrsvxk)
  → POST /api/auth/from_external (VOLAURA Railway, X-Bridge-Secret)
  → shadow user created in dwdgzfusjsobnixgyzjk
  → shared_jwt returned
  → POST /api/character/events (focus sessions, XP earned)
  → crystal_earned event → visible in Life Simulator

VOLAURA assessment complete
  → AURA score upserted (upsert_aura_score RPC)
  → badge_tier computed
  → crystal_earned emitted → character_events table
  → Life Simulator reads character_events
```

## Crystal Economy

All products write to `character_events` table (shared Supabase):

| Source | Event type | Crystals |
|---|---|---|
| VOLAURA assessment | `xp_earned` | +50–200 |
| MindShift focus session | `xp_earned` | +10–30 |
| VOLAURA badge earned | `buff_applied` | +100 |

## ZEUS Gateway

Python swarm (localhost) → `POST /api/zeus/proposal` (Railway)
Auth: `X-Gateway-Secret` header

Proposals written to `memory/swarm/proposals.json` (local, gitignored).

## Key Secrets (cross-product)

| Secret | Lives in | Used by |
|---|---|---|
| `EXTERNAL_BRIDGE_SECRET` | Railway + MindShift edge fn | volaura-bridge-proxy ↔ /api/auth/from_external |
| `GATEWAY_SECRET` | Railway + local .env | autonomous_run.py → /api/zeus/proposal |
| `SUPABASE_JWT_SECRET` | Railway | Minting shared JWTs for bridged users |

## Constitution

All products governed by `docs/ECOSYSTEM-CONSTITUTION.md` v1.7.
5 Foundation Laws apply everywhere:
1. NEVER RED — errors = purple
2. Energy Adaptation — Full/Mid/Low modes
3. Shame-Free Language
4. Animation Safety (max 800ms)
5. One Primary Action per screen
