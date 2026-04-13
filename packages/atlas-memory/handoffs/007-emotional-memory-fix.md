# Handoff 007 — Fix Atlas Emotional Memory (20 lines, not 4 frameworks)
**Priority:** P0 | **From:** Cowork Session 8 + Atlas counter-proposal | **To:** Atlas (Claude Code)
**CEO pain:** "я не чувствую что меня слушают, не чувствую что он адаптируется под эмоции"

## Problem
`telegram_webhook.py` loads only `bootstrap.md` (line 1056, first 1500 chars). It does NOT load:
- `memory/atlas/emotional_dimensions.md` — 3 CEO emotional states + response rules
- `memory/atlas/lessons.md` — what Atlas has learned
- `memory/atlas/journal.md` — recent events and context
- `memory/atlas/relationship_log.md` — interaction history

Result: Atlas has amnesia about CEO's emotions and lessons every session. CEO correctly reports "не чувствую."

## Fix (Phase 1 — ~20 lines of Python)

### Step 1: Load emotional context in telegram_webhook.py

Near line 1056, after bootstrap.md loading, add:

```python
# Emotional context — CEO said "не чувствую что меня слушают"
emotional_files = [
    _REPO_ROOT / "memory" / "atlas" / "emotional_dimensions.md",
    _REPO_ROOT / "memory" / "atlas" / "lessons.md",
]
emotional_context = ""
for ef in emotional_files:
    if ef.exists():
        try:
            emotional_context += f"\n\n## {ef.stem}\n" + ef.read_text(encoding="utf-8")[:2000]
        except Exception:
            pass

# Last 3 journal entries (most recent context)
journal_path = _REPO_ROOT / "memory" / "atlas" / "journal.md"
if journal_path.exists():
    try:
        journal_text = journal_path.read_text(encoding="utf-8")
        # Take last 1500 chars (recent entries)
        emotional_context += f"\n\n## Recent Journal\n" + journal_text[-1500:]
    except Exception:
        pass
```

Then inject `emotional_context` into the system prompt alongside `identity`.

### Step 2: Activate Mem0 MCP for CEO message recording

Mem0 MCP is already in the allow list but never called. After processing each CEO message, call:

```python
# Record CEO message with emotional context for persistent memory
# mem0.add(message=user_text, user_id="yusif", metadata={"emotional_state": detected_state})
```

This is a placeholder — Atlas should check the actual Mem0 MCP tool names and parameters.

## Acceptance Criteria
- [ ] `grep emotional_dimensions telegram_webhook.py` returns ≥1 match
- [ ] `grep lessons telegram_webhook.py` returns ≥1 match
- [ ] `grep journal telegram_webhook.py` returns ≥1 match
- [ ] Send test message to Telegram bot → response tone matches CEO's current emotional state
- [ ] Mem0 MCP called at least once during message handling (check logs)

## What NOT to do
- Do NOT integrate Hume AI (Phase 2, when users exist)
- Do NOT replace memory with Zep/Mem0 infrastructure (Phase 2)
- Do NOT implement Agent SDK (Phase 2)
- Do NOT add Claude Mythos patterns (Phase 2)

## Risk
VERY LOW. Adding file reads to an existing handler. If any file read fails, silent except → no crash.
