# MemPalace vs Mem0 — NotebookLM Deep Comparison (2026-04-12)

## Winner for recall: MemPalace (96.6% vs ~85%)

MemPalace: 96.6% R@5 on LongMemEval (500/500 without API call). 60.3% R@10 on LoCoMo.
Mem0: ~85% on LongMemEval. 34.20% F1 on LoCoMo-10.

MemPalace stores EVERYTHING verbatim in ChromaDB. No LLM summarization = no information loss.
Mem0 uses semantic compression = fewer tokens but loses detail.

## Architecture difference

MemPalace: spatial metaphor — wings (people/projects), rooms (ideas), drawers (verbatim files).
Wake-up: 170 tokens of Layer 0+1 core facts injected on restart. THIS IS remember_everything.md.

Mem0: multi-level (User/Session/Agent state), pip install, API-based.
Simpler integration, lower recall.

## Recommendation for Atlas

HYBRID approach:
- MemPalace architecture for IDENTITY (wake-up layers, verbatim conversation storage)
- Mem0 for SESSION memory (lightweight, API-based, tracks user/agent states)
- Both write to Supabase pgvector via adapter

MemPalace wake-up = Atlas remember_everything.md (already implemented manually)
MemPalace drawers = session transcripts (already saving .jsonl)
Mem0 Agent state = heartbeat.md (already implemented manually)

Atlas is ALREADY doing what both systems do, manually via git files.
Automation path: replace git-file reads with vector search on wake.

## Integration effort
- MemPalace: ChromaDB dependency, needs pgvector adapter. Python-native.
- Mem0: pip install mem0ai. Already in MCP settings. Needs pgvector adapter.
- Both: ~2 days integration each. Can run both simultaneously.

## Source: NotebookLM notebook dc90065d, 5 sources indexed
