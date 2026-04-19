## Acceptance Criteria
- [x] All 4 LLM providers have unit tests (Vertex, Gemini, Groq, OpenAI)
- [x] Fallback chain tested (timeout + exception → next provider)
- [x] JSON/text response modes tested for each provider
- [x] Singleton client lifecycle tested (lazy init + reset)
- [x] Embedding function tested (Vertex primary + Gemini fallback)
- [x] Full backend suite passes with zero regressions
