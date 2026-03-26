-- Migration: Store gaming analysis results at completion time
-- Sprint 8, Session 33 — Fix: get_results() re-ran antigaming.analyse() instead of reading stored values
-- Problem: If thresholds change in future, get_results() could show different penalty than what was applied to AURA
-- Fix: Store penalty_multiplier and flags at complete time, read them back in get_results()

ALTER TABLE public.assessment_sessions
    ADD COLUMN IF NOT EXISTS gaming_penalty_multiplier FLOAT NOT NULL DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS gaming_flags TEXT[] NOT NULL DEFAULT '{}';

COMMENT ON COLUMN public.assessment_sessions.gaming_penalty_multiplier IS
    'Anti-gaming penalty applied at completion time (0.0-1.0). Stored to prevent inconsistency if thresholds change.';

COMMENT ON COLUMN public.assessment_sessions.gaming_flags IS
    'Anti-gaming flags detected at completion (e.g. excessive_rushing, alternating_pattern). Immutable after completion.';
