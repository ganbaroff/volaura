# AGENTS.md — apps/tg-mini

**Parent manifest:** [../../AGENTS.md](../../AGENTS.md)

## Scope

Telegram Mini App surface for VOLAURA ecosystem touchpoints.

## May depend on

- `packages/*` shared configs
- VOLAURA API via HTTP

## May NOT depend on

- `apps/api/app/*` Python internals, `packages/swarm/`

## Tests

- `pnpm test` and `pnpm build` from `apps/tg-mini/` (CI tg-mini job)
