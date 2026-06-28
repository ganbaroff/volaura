# AGENTS.md — apps/web

**Parent manifest:** [../../AGENTS.md](../../AGENTS.md)

## Scope

Next.js 14 App Router user-facing UI for VOLAURA. AZ-primary i18n, Zustand, TanStack Query.

## May depend on

- `packages/*` (shared configs, types via generated API client)
- `apps/api/` **via HTTP only** (never import Python)

## May NOT depend on

- `packages/swarm/`, `apps/api/app/*` internals, server-side Python

## Error handling

- Structured API errors: unwrap `.data`, show purple `#D4B4FF` for errors (Constitution Law 1)
- Absolute routes: `/${locale}/path`

## Tests

- Vitest in `apps/web/` (`pnpm vitest run`)
- Launch-critical hooks covered in `.github/workflows/ecosystem-hard-gates.yml`
