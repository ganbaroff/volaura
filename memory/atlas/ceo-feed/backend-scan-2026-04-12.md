# VOLAURA Backend Architecture Scan (2026-04-12)

## 119 endpoints across 24 routers
Top: organizations (15), events (12), admin (10), profiles (9), tribes (9)
Assessment: 8 endpoints (start, answer, complete, results, coaching, info)
Cross-product: auth_bridge (1), character (4), zeus_gateway (2)

## IRT/CAT Engine (362 lines, engine.py)
3PL model: P(correct|theta) = c + (1-c) / (1 + exp(-a*(theta-b)))
EAP estimation with 49-point quadrature grid
Fisher Information maximization for item selection
15% epsilon-greedy random exposure (anti-gaming)
Energy Adaptation: full(20q), mid(12q), low(5q)

## LLM Fallback Chain (V-BRAIN)
1. Vertex AI Express (99.9% SLA)
2. Gemini 2.5 Flash (free, 15 RPM)
3. Groq llama-3.3-70b (14,400/day free)
4. OpenAI GPT-4o-mini (paid last resort)
5. Keyword fallback (bars.py)
PII redactor NOW in place (this sprint's commit 07cf128)

## 79 migrations applied
Recent critical: zeus_governance, zeus_harden, health_data_firewall, user_identity_map

## Security hardening
JWT validation via service role (not anon key — CVSS 9.1 fix)
Admin client singleton (double-checked locking)
Kill switches: payment, email, swarm (all default OFF)
5 hard-fail startup guards + 7 warnings

## Middleware stack
RequestId, SecurityHeaders, ErrorAlerting→Telegram, RateLimit, ProxyHeaders, CORS

## Python Swarm (94 files in packages/swarm/)
engine.py: SwarmEngine v7 — tournament mode, skill augmentation, reasoning graphs
autonomous_run.py: daily ideation, 8 perspectives, writes proposals
agent_hive.py: per-agent lifecycle, competency exams, status ladder

## Known bugs in code (grep BUG)
BUG-QA-021: EAP sd guard
BUG-009: total_seconds() not .days
BUG-010: expired session rejection
BUG-015: idempotent completion
BUG-001: single UPDATE race fix

## 46 test suites
IRT engine, E2E assessment, auth, blind cross-assessment, decay, character, admin, regression

## Maturity: pre-launch MVP with kill switches active
