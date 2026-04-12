# MindShift (MindFlow) — Deep Scan Results (2026-04-12)

## Product: AI productivity app for ADHD professionals
Flutter 3.5+ mobile/web + Python 3.11 Telegram bot + Supabase + Gemini 2.0 Flash

## 5 modules built: Brain Dump, Chat, Vault, Focus, Finance
Offline-first (Hive local cache), Realtime sync, Telegram voice transcription

## P0 bugs FIXED (per audit Feb 28):
- Supabase list_users type mismatch — fixed
- ai_reminders schema inconsistency (message vs title) — fixed  
- Flutter widget test broken — fixed

## Integration with VOLAURA: ZERO
No bridge client, no event emission, no character_events, no crystal economy.
VOLAURA built receiving end (EXTERNAL_BRIDGE_SECRET, health_data_firewall).
MindShift never built sending end. This is ONE-DIRECTIONAL.

## Prompt routing: 4 tags
#task → PMP action plans, #dump → brain dump structuring, #linkedin → posts, #azlife → game specs
Default → universal AI assistant. Contract in docs/prompt_routes.md.

## 3D agents: NOT FOUND in MindShift
CEO mentioned 3D agents — not in mindflow/ repo. May be in separate project or planned.

## Architecture: solid but needs testing
BaseSyncRepository pattern (Hive + Supabase + Realtime merge).
No component-level specs. n8n optional but not documented for setup.

## Deployment: Cloud Run (bot), Firebase Hosting (web), GitHub Actions CI
Secrets: GEMINI_API_KEY, MINDFOCUS_BOT_TOKEN, SUPABASE_* vars

## Key gap: no VOLAURA bridge = ecosystem promise unfulfilled
The "one user, five touchpoints" vision requires MindShift → VOLAURA event flow.
Without it: no crystal earning from focus sessions, no cross-product AURA enrichment.
