# NotebookLM Research: Memory Systems for Atlas — 2026-04-12

## Verdict: Mem0 is the best fit for VOLAURA stack

### Comparison (from NotebookLM with 4 source repos indexed)

**Mem0** — path of least resistance
- `pip install mem0ai`, works with Python 3.11
- Multi-Level Memory: User + Session + Agent state tracking
- 90% fewer tokens than full-context methods
- Vector store adapter needed for Supabase pgvector (no native support)
- Already configured in settings.local.json as MCP

**SimpleMem** — best architecture, worst fit
- Requires Python 3.10 strictly (we use 3.11)
- Cross-session memory with auto-injection — exactly what Atlas needs
- Semantic compression prevents redundant fragmentation
- But: tightly coupled to LanceDB + SQLite, would need full rewrite for pgvector

**MemOS** — overengineered for current needs
- Full memory OS with Neo4j + Qdrant dependencies
- Redis Streams for async ingestion
- Overkill: we need persistent identity, not a memory database cluster

### Integration plan for Mem0
1. Install mem0ai in apps/api
2. Write pgvector adapter (Supabase vector store instead of default)
3. Store Atlas session/agent memories via Mem0 API
4. Query relevant context on wake instead of reading 22 files
5. Expected token reduction: 50-70% per session start

### Source: NotebookLM notebook dc90065d, 4 GitHub repos indexed
