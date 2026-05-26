# 08 — WP-2A Safe Subset (Manual Execution)

Date: 2026-05-26

## Why WP-2 was split

Full WP-2 proposed deleting 14 files as duplicates. Re-validation on the live tree showed most pairs are no longer identical, so broad deletion is unsafe.

## Re-validation result (sample set)

- `DIFFERS`: 8 pairs
- `MISSING`: 1 pair (after deletion below)
- `IDENTICAL`: 0 remaining in the checked set

Command used:

```powershell
$pairs=@(
  @('docs/archive/root-superseded/500-HOUR-PLAN.md','docs/500-HOUR-PLAN.md'),
  @('docs/archive/root-superseded/CONSTITUTION_AI_SWARM.md','docs/CONSTITUTION_AI_SWARM.md'),
  @('docs/archive/root-superseded/BETA-INVITE-TEMPLATES.md','docs/BETA-INVITE-TEMPLATES.md'),
  @('docs/archive/stitch/STITCH-DESIGN-SYSTEM.md','docs/design/STITCH-DESIGN-SYSTEM.md'),
  @('.claude/agents/analysis/code-review/analyze-code-quality.md','.claude/agents/analysis/analyze-code-quality.md'),
  @('.claude/agents/data/ml/data-ml-model.md','.claude/agents/data/data-ml-model.md'),
  @('.claude/agents/development/dev-backend-api.md','.claude/agents/development/backend/dev-backend-api.md'),
  @('.claude/agents/devops/ops-cicd-github.md','.claude/agents/devops/ci-cd/ops-cicd-github.md'),
  @('.claude/agents/documentation/docs-api-openapi.md','.claude/agents/documentation/api-docs/docs-api-openapi.md'),
  @('.claude/agents/specialized/spec-mobile-react-native.md','.claude/agents/specialized/mobile/spec-mobile-react-native.md')
)
```

## WP-2A action executed

Removed one confirmed identical duplicate:

- Deleted: `.claude/agents/analysis/code-review/analyze-code-quality.md`
- Canonical kept: `.claude/agents/analysis/analyze-code-quality.md`

Command:

```bash
git rm .claude/agents/analysis/code-review/analyze-code-quality.md
```

## Next

Proceed with WP-2B as a **pair-by-pair semantic review**, not bulk deletion.
