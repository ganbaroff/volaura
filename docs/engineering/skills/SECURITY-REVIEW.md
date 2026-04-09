# Security Review Skill — Volaura Edition
# Source: everything-claude-code (affaan-m) + Volaura-specific additions
# Use this: any session touching auth, input, API endpoints, DB, or deployments

## When to Trigger
- Implementing auth or session handling
- Any user input reaches the DB or LLM
- New API endpoints added
- File upload or media handling
- Payment/subscription features
- Third-party integrations
- Before every deploy

## 10-Point Security Checklist

### 1. Secrets Management ✓
- [ ] No API keys, tokens, or passwords in source code
- [ ] All secrets in `.env` (git-ignored, `.env.example` committed instead)
- [ ] Supabase service key NEVER in frontend code
- [ ] `NEXT_PUBLIC_` prefix ONLY for truly public values
- [ ] `apps/api/.env` and `apps/web/.env.local` both git-ignored

### 2. Input Validation ✓
- [x] All user inputs validated with Pydantic v2 `field_validator`
- [x] HTML stripped from text inputs (prevent XSS + LLM prompt injection)
- [x] UUID validation on all ID params
- [x] Max length enforced on all text fields (5000 chars for answers, 500 for names)
- [x] Path params bounded: `TokenParam = Annotated[str, Path(max_length=100)]`
- [x] File uploads: size limit (5MB), type whitelist (if applicable)
- [x] Input validation implemented for all API endpoints

### 3. SQL / DB ✓
- [ ] ONLY Supabase SDK query builder — no raw SQL string concatenation
- [ ] RLS enabled on ALL tables (no exceptions)
- [ ] RLS policies cover: read own, write own, org-scoped, public read
- [ ] No direct PostgREST for vector ops — use RPC functions only

### 4. Auth & Authorization ✓
- [ ] JWT verified server-side: `admin.auth.get_user(token)` — NEVER `jwt.decode(token, anon_key)`
- [ ] anon key is PUBLIC — never treat it as a secret
- [ ] Per-request Supabase client via `Depends()` — NEVER global client
- [ ] Role-based access: volunteer vs org coordinator vs admin
- [ ] Check-in endpoints: only org owner authorized (not volunteer self-checkin)
- [ ] `?next` redirect param validated: must start with `/` (prevent open redirect)

### 5. XSS Prevention ✓
- [ ] Never use `dangerouslySetInnerHTML` without DOMPurify
- [ ] User-generated content sanitized before render
- [ ] CSP headers configured in security_headers.py middleware
- [ ] `noopener noreferrer` on all `window.open()` calls

### 6. CSRF Protection ✓
- [ ] Supabase auth uses httpOnly cookies (handled by Supabase SDK)
- [ ] SameSite cookie attribute set
- [ ] State-changing operations require authenticated session

### 7. Rate Limiting ✓
- [x] Auth endpoints: 5/min (already implemented via slowapi)
- [x] Assessment start: 3/hour
- [x] Assessment answer: 60/hour
- [x] Verification token generation: add limit if not present
- [x] LLM endpoints: rate limit to prevent cost abuse
- [x] Rate limiting implemented for all API endpoints

### 8. Sensitive Data ✓
- [ ] Never log passwords, tokens, or PII
- [ ] `logger.info(...)` — never log request bodies containing credentials
- [ ] API errors return generic messages (not stack traces) in production
- [ ] `app_env: production` → no debug info in responses

### 9. Dependency Security ✓
- [ ] `pnpm audit` — no critical vulnerabilities
- [ ] `pip install safety && safety check` — no known CVEs
- [ ] Lock files committed (`pnpm-lock.yaml`, `requirements.txt`)
- [ ] No abandoned packages (check last release date + GitHub stars)

### 10. Agentic / LLM Security (Volaura-specific) ✓
- [ ] User assessment answers sanitized BEFORE sending to Gemini (prevent prompt injection)
- [ ] LLM responses validated: score must be 0-100, structured JSON only
- [ ] Token max_tokens set on all LLM calls (prevent runaway generation)
- [ ] LLM fallback chain: Gemini → OpenAI → keyword scoring (never fail silently)
- [ ] Verification tokens: single-use (token_used guard), TOCTOU protection on UPDATE

## Volaura Critical Path (CVSS 9.1 was caught here)

The highest-risk flow is:
```
User input → LLM evaluation → AURA score write → Badge tier change
```

For any change touching this path, ALL 10 points must pass before merge.

## Severity Scale
- **P0 (fix before next commit):** Exposed secrets, auth bypass, SQL injection, open redirect
- **P1 (fix this session):** Missing rate limit, unvalidated input, XSS vector
- **P2 (fix next session):** Missing audit log, weak error messages, dependency with CVE
- **P3 (backlog):** Defense-in-depth improvements, monitoring gaps
