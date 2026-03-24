# Prompt Modules

This directory contains reusable prompt templates and architecture state documentation for the MiroFish swarm engine.

## Files

- `architecture_state.md` — Current architecture and design patterns
- `current_gaps.md` — Known gaps and improvement opportunities

## Adding New Prompt Modules

When creating a new prompt module:

1. Create a markdown file with a clear, descriptive name (e.g., `social_reaction.md`)
2. Document the prompt's purpose, inputs, and expected outputs
3. Include example outputs if applicable
4. Add to the appropriate section in `architecture_state.md`
5. Update `current_gaps.md` if this module addresses a known gap

## Naming Convention

Use snake_case filenames that match the agent/evaluator they support:
- `social_reaction.md` — Social media reaction simulator
- `architecture_audit.md` — Architecture evaluation
- `cto_review.md` — Code quality and design review
