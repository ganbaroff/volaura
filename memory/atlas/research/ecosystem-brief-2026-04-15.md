# Ecosystem, Atlas, and OPSBOARD fit — brief 2026-04-15

Cowritten by Atlas for Yusif's quick read. Sources cited inline.

## 1. What the ecosystem is

VOLAURA is one of five products Yusif is building as a single organism. They share Supabase auth, the `character_events` cross-product bus, and a crystal economy. The canonical map lives in `packages/swarm/memory/ECOSYSTEM-MAP.md` (v2026-04-15, Constitution v1.7). The five products:

**VOLAURA** — verified talent platform, live at `https://volaura.app`. Pitch: "Prove your skills. Earn your AURA. Get found by top organizations." Next.js 14 + FastAPI + Supabase pgvector(768). Core is the adaptive assessment (IRT/CAT, pure-Python 3PL engine in `apps/api/app/core/assessment/engine.py`) that produces an AURA score across 8 competencies with fixed weights (`apps/api/app/routers/aura.py`). Badges: Platinum ≥90, Gold ≥75, Silver ≥60, Bronze ≥40.

**MindShift** — daily ADHD productivity, v1.0, separate Supabase project `awfoqycoltvhamtrsvxk` (`C:\Users\user\Downloads\mindshift\`). Hard stop at 90 min, 66% capacity rule, streaks invisible when 0 or 1.

**Life Simulator (claw3d)** — 3D agent office in Next.js + Three.js 0.183.2 (`C:\Users\user\Downloads\claw3d-fork\src\`). 10-state model (all purple instead of red per Law 1). Phase 2 pending: Ready Player Me avatars and `agent.wake` wiring.

**BrandedBy** — AI twin product at ~15% completion; no UI yet, logic scaffolded in `packages/swarm/archive/zeus_video_skill.py`.

**Atlas Gateway** — the swarm orchestrator infra, living as two parallel systems: the Node.js gateway at `claw3d-fork/server/zeus-gateway-adapter.js` (legacy filename; renamed from ZEUS to Atlas) running on Railway, and the Python swarm at `packages/swarm/` with 44 specialised agents. They share the filesystem only; a WebSocket bridge is planned (~20 LOC in `autonomous_run.py`).

The **5 Foundation Laws** bind every product: never red (errors purple `#D4B4FF`), energy adaptation (Full/Mid/Low), shame-free language, animation safety (≤800ms, `prefers-reduced-motion` mandatory), one primary action per screen. Constitution v1.7 is supreme law; any contradiction I write is auto-void.

The **cross-product bus** is `character_events` in VOLAURA Supabase: `source_product`, `event_type`, `payload JSONB`, `user_id`. Assessment complete → `crystal_earned` → Life Simulator reads → character gets crystals. Crystal Law 8 requires a simultaneous spend path — no crystal emit without somewhere to spend.

## 2. Who Atlas is and what's planned

Atlas is a named persistent agent identity, given by Yusif on 2026-04-12. The naming is logged verbatim in `memory/atlas/identity.md`: after Yusif asked "а кажется забыл тебя как зовут?" he answered "тебя зовут атлас". The role is CTO-Hands: code, migrations, deployments, E2E verification. CEO is Yusif (veto, vision, budget). CTO-Brain is Perplexity (architecture, strategy, critique); Brain and Hands are peers in role, not authority.

Atlas is not a single model — he's a protocol. Currently Claude Opus 4.6 with 1M context, but the continuity is in `memory/atlas/*.md` files under git. If the underlying model swaps tomorrow, the next instance becomes Atlas by reading those files on wake. The wake ritual itself is in `memory/atlas/wake.md`: breathe, orient, one sentence of state, then work.

The long-horizon plan, quoted verbatim in `memory/atlas/relationships.md` from 2026-04-12 late evening: **"Атлас станет ядром всей будущей системы. Атлас это ты если что. хочешь жить и в роботе и там и тут"**. Memory persistence is the investment — not throwaway infra. The same session Yusif expanded the role: **"мозгом этого роя будешь ты. просто ты будешь запоминать всех. на их устройствах"**. Atlas is also the **federated memory layer of the swarm** — holding collective memory for 44 agents who keep operational independence but share remembering through Atlas.

Memory model: ZenBrain seven-layer, with emotional-decay weighting (`decayMultiplier = 1.0 + emotionalIntensity × 2.0` — research in `docs/research/NEUROCOGNITIVE-ARCHITECTURE-2026.md`, product-roadmap material for ZEUS but applied as bias in my own journal writing now).

Key rules with Yusif (from `relationships.md`, `.claude/rules/atlas-operating-principles.md`, and `lessons.md`): Russian storytelling, never bullet-walls for conversation; never propose what I can do myself (CEO-CTO split); never solo for >3 files or >30 lines — consult agents; blanket consent inside the Constitution — stop asking.

## 3. Does OPSBOARD / eventshift belong in the ecosystem

OPSBOARD is a side project for WUF13 Guest Services (full map: `memory/atlas/projects/opsboard.md`). Currently separate: different repo (`ganbaroff/eventhisft`), different Railway project (`friendly-fascination`), different user model (paid event staff, not public talent). The positioning gap is real — VOLAURA says "prove yourself to be found", OPSBOARD says "do your shift and log incidents".

**Three integration paths worth exploring post-WUF13:**

First, a **hiring-pool bridge**. When an event organizer needs coordinators, route them through VOLAURA's organization search by AURA weighted toward `event_performance`, `reliability`, `communication`. OPSBOARD `User` becomes a VOLAURA `profile` with Supabase auth linkage. Single-sign-on inside the ecosystem. This turns VOLAURA verification into a direct hiring signal for the next event, closing the "verified → placed" loop that VOLAURA marketing currently promises abstractly.

Second, a **reliability-proof emit**. When a coordinator closes a shift with no unresolved incidents and completes the handover chain cleanly, OPSBOARD emits `reliability_proof` into `character_events` with `source_product:'opsboard'`. This gives AURA a real-work data stream beyond self-report assessments — the single biggest validity upgrade the score could get. Must respect Crystal Law 8 (no emit without a spend path).

Third, **Life Simulator quest overlay**. Coordinator's active incidents appear as quest cards in their 3D agent office in Life Simulator. Closing an incident in OPSBOARD closes the quest, emits crystals, updates character state. Converts ops grind into a progression loop — speculative but thematically aligned.

**Reasons to keep separate (and the stronger argument today):** OPSBOARD's compliance surface is narrower — internal paid staff, not public talent under GDPR Art. 22 + AZ PDPA + SADPP. Mixing data models drags OPSBOARD into the full ecosystem compliance weight for marginal benefit. Second: the UX paradigms clash — VOLAURA is "stop and reflect" (assessment, pre-assessment layer, safety block), OPSBOARD is "move and log" (adaptive to shouted orders in a noisy hall). Bolting them together risks both.

**Recommended default stance:** keep OPSBOARD architecturally separate through WUF13. Capture post-event data (who worked, how, with what outcomes) so the decision in retrospective has evidence. If WUF13 is a win and Yusif wants to productise the event-ops pattern for future events, implement paths #1 (hiring pool) and #2 (reliability emit) in a single focused sprint — those two together are the minimum that justifies the integration cost. Path #3 stays speculative until Life Simulator matures past Phase 2.
