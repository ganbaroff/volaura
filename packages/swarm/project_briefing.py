"""Project Briefing — single source of factual constants for all swarm agents.

Every agent (autonomous_run, coordinator, debate scripts) imports PROJECT_FACTS
so they share the same ground truth about AURA weights, tech stack, and
ecosystem layout. This prevents hallucination of wrong competency weights
or contradicting the locked positioning rules.

Added: Session 122 (2026-04-21) — test revealed Cerebras hallucinated
communication weight as 12% and invented "Technical Proficiency" competency.
"""

from __future__ import annotations

PROJECT_FACTS = """## PROJECT FACTS (hardcoded — never contradict)
Platform: VOLAURA — verified professional talent platform
NEVER say "volunteer" or "LinkedIn competitor". Positioning: "Prove your skills. Earn your AURA. Get found by top organizations."

AURA Score Weights (FINAL — locked in CLAUDE.md):
  communication: 0.20 | reliability: 0.15 | english_proficiency: 0.15 | leadership: 0.15
  event_performance: 0.10 | tech_literacy: 0.10 | adaptability: 0.10 | empathy_safeguarding: 0.05

Badge Tiers: Platinum ≥90 | Gold ≥75 | Silver ≥60 | Bronze ≥40
TAM: 500-700K in AZ. B2B before B2C (LTV/CAC broken at $3/mo B2C). Birbank/m10 before Stripe.

Ecosystem (5 faces, one Supabase auth + character_events table):
  VOLAURA (assessment) · MindShift (focus/ADHD) · Life Simulator (Godot 4)
  BrandedBy (AI twin) · ZEUS (agent framework)

Tech Stack:
  Backend: Python 3.11+ FastAPI async, Supabase SDK per-request Depends(), Pydantic v2, loguru
  Frontend: Next.js 14 App Router, TypeScript strict, Tailwind CSS 4, Zustand, TanStack Query
  Database: Supabase PostgreSQL + RLS + pgvector(768) Gemini embeddings
  Hosting: Vercel (frontend), Railway (backend), Supabase (DB)
  LLM hierarchy: Cerebras Qwen3-235B → Ollama local → NVIDIA NIM → Anthropic Haiku (NEVER Claude as swarm agent)

Foundation Laws (supreme — 5 laws, ECOSYSTEM-CONSTITUTION.md):
  1. No red errors (use #D4B4FF purple errors, #E9C400 amber warnings)
  2. Energy modes: Full / Mid / Low (all UI must support all 3)
  3. Shame-free language (no "you failed", no %, no streaks as punishment)
  4. Animation ≤800ms + prefers-reduced-motion
  5. One primary CTA per screen
"""
