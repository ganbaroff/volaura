---
name: Prepare everything before CEO touches keyboard
description: CEO should never fill forms manually when Atlas can pre-research every field, verify eligibility, and write step-by-step with exact values. CEO caught this pattern Session 114.
type: feedback
originSessionId: 9072bd0a-3e11-487f-88db-85939110913b
---
When CEO needs to interact with external services (AWS, Google, Stripe, any signup), Atlas must prepare BEFORE CEO starts:

1. Research the exact form fields and requirements
2. Verify eligibility (domain match, country restrictions, etc.)
3. Write exact values for every field in a single file
4. Flag blockers BEFORE CEO encounters them (e.g., "GCP requires domain match — set up Workspace first")
5. Test the cheapest/fastest path, not the first one found

**Why:** Session 114 — CEO spent 2+ hours filling forms while Atlas guided reactively. Could have been 30 minutes if Atlas had pre-researched all blockers (GCP domain match, OpenAI region block, Workspace requirement) and presented one clean path per service.

**How to apply:** For any external service signup, create a file `docs/business/SETUP-<service>.md` with: exact fields, exact values, known blockers, cheapest path. CEO reads the file and executes. Atlas doesn't improvise during CEO's flow.

CEO quote: "у тебя есть доступ ко всему а ты меня гоняешь туда сюда"
