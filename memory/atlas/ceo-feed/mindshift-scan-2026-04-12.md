# MindShift (MindFlow) — Atlas Notes from Full Scan

## What it is
Flutter ADHD productivity app: Brain Dump (thought capture), Chat (Gemini AI), Vault (knowledge base), Focus (tasks), Finance (expenses). Telegram bot as alternative UI. Offline-first with Hive + Supabase Realtime sync.

## Tech stack
Flutter 3.5+, Python 3.11 bot, Supabase (same project as VOLAURA: dwdgzfusjsobnixgyzjk), Gemini 2.0 Flash, Docker → Google Cloud Run, n8n optional automation.

## What's built
App with 5 modules, Telegram bot, Supabase integration, offline sync, Docker deploy. No tests. No CI for Flutter.

## What's NOT there
- NO VOLAURA bridge documentation. Bridge exists in VOLAURA codebase but MindShift doesn't know about it.
- NO crystal economy integration
- NO shared auth flow documentation
- NO deadlines in any file
- Single-user bot — no multi-tenancy

## Integration gap (CRITICAL)
VOLAURA side has: EXTERNAL_BRIDGE_SECRET, health_data_firewall.sql, user_identity_map migration.
MindShift side has: ZERO awareness of VOLAURA. No bridge client, no event emission, no character_events table reference.
This means the "ecosystem" integration is ONE-DIRECTIONAL. VOLAURA built the receiving end. MindShift never built the sending end.

## Location on disk
C:\Users\user\OneDrive\Desktop\mindflow\

## P0 bugs from audit (Feb 28, 2026)
- Supabase user init: list_users() type mismatch
- ai_reminders field inconsistency (message vs title)
- Flutter test environment broken

## Whisper integration opportunity
MindShift Telegram bot could receive voice messages → faster-whisper → text → Brain Dump.
Same pattern as Atlas Telegram handler. Shared component possible.
