# VOLAURA Agents Index

## Active 15 (proven, MindShift-derived + VOLAURA-specific)

### Quality & Security
- **a11y-scanner** — WCAG 2.2 AA audits, focus rings, ARIA
- **sec** — Security: auth, RLS, edge function secrets, GDPR, OWASP
- **security-auditor** — VOLAURA-specific security audit
- **code-reviewer** — Code quality, ADHD-safe patterns
- **guardrail-auditor** — Pre-commit scan vs Constitution rules
- **qa-quality-gate** — Definition of Done enforcement

### Build & Deploy
- **build-error-resolver** — TypeScript + FastAPI + pnpm build errors
- **bundle-analyzer** — Bundle size, lazy-loading verification
- **infra** — Vercel + Railway + Supabase + GitHub Actions
- **liveops** — Production health, post-deploy SRE

### Architecture & Product
- **architect** — System design, monorepo patterns
- **ecosystem-auditor** — Cross-product impact (5-product mesh)
- **product-ux** — User flows, retention, ADHD-safe
- **growth** — Retention signals, funnel drop-offs

### Testing
- **e2e-runner** — Playwright E2E for apps/web

## Legacy directories (kept for reference, mostly unused)

- `analysis/`, `architecture/`, `browser/`, `consensus/`, `core/`, `custom/`,
  `data/`, `development/`, `devops/`, `documentation/`, `flow-nexus/`, `github/`,
  `goal/`, `optimization/`, `payments/`, `sona/`, `sparc/`, `specialized/`,
  `sublinear/`, `swarm/`, `templates/`, `testing/`, `v3/`

These came from claude-flow framework and are not actively invoked.
Decision pending: keep, archive, or delete.

## Python swarm (separate system)

44 agents live in `packages/swarm/` (Python). They run on cron via
`.github/workflows/swarm-daily.yml`. They are NOT the same as `.claude/agents/`
above — these are autonomous background workers, the `.claude/agents/` are
on-demand specialists invoked from Claude Code sessions.
