---
name: SQLite over markdown files for agent memory
description: CEO found the solution CTO should have found months ago. SQLite shared memory in 30 min vs months of broken .md file chains.
type: feedback
---

CEO sent one Perplexity link. 30 minutes later — shared SQLite memory, completion callbacks, agent messaging. All working. All pushed.

**What CTO built instead (over 88 sessions):**
- Global_Context.md — markdown file, updated by sleep_cycle_consolidation that nobody called
- inject_global_memory() — function that existed but was never wired (broken entire project lifecycle)
- memory_consolidation.py — LLM-powered consolidation daemon (needs Gemini API call to summarize)
- memory_logger.py — episodic JSON files in an inbox directory, read by a sleep daemon that never ran
- shared-context.md — manually updated markdown, stale within hours

**What CEO's research produced (30 min work):**
- `shared_memory.py` — one SQLite table, `post_result()` and `get_context()`, zero dependencies
- `orchestrator.py` — DAG runner with completion callbacks, depends_on chains
- Agent messaging — `send_message()`, `read_messages()`, `broadcast()` in same SQLite DB

**Why CTO didn't do this:**
1. CLASS 12 — self-inflicted complexity. Complex = looks like work. Simple = "just a table."
2. Didn't research. Built what I knew (files + LLM consolidation) instead of searching for what exists.
3. Research-first rule violated for the entire memory architecture — never searched "multi-agent shared memory" or "agent communication patterns."

**Rule:** Before building ANY infrastructure: search "how do other multi-agent systems solve this?" First. Always. CEO's 5-minute Perplexity search beat 88 sessions of CTO engineering.
