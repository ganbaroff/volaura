---
description: Secret key handling — auto-save to .env when seen in chat
---

# Secret Key Protocol

## Rule: When Yusif shares a key in chat → IMMEDIATELY save it

When any API key, token, secret, or credential appears in the conversation:

1. **Save to `apps/api/.env`** with a comment explaining what it is and why
2. **Update `.env.md`** — add row to the relevant table
3. **Confirm in reply**: "Saved [KEY_NAME] to apps/api/.env — [what it's for]"

NEVER leave a key floating in the chat. NEVER ask Yusif to "add it manually".

## Format for .env entry
```
# [SERVICE] — [what it does] — added [date]
KEY_NAME=value
```

## Example
User pastes: `7123456789:AAGxxx...`
Claude immediately:
- Identifies as Telegram bot token (7-digit ID + colon + alphanumeric)
- Writes to apps/api/.env: `TELEGRAM_BOT_TOKEN=7123456789:AAGxxx...`
- Adds comment: `# Telegram — @volaurabot — agent autonomy notifications to CEO`
- Confirms: "Saved TELEGRAM_BOT_TOKEN to .env"

## Key Recognition Patterns
| Pattern | Key type |
|---------|---------|
| `sk-proj-...` | OpenAI |
| `sk-...` (32 chars) | Anthropic |
| `AIzaSy...` | Google/Gemini |
| `gsk_...` | Groq |
| `sk-or-...` | OpenRouter |
| `[7-10 digits]:AA...` | Telegram bot token |
| `[7-10 digit number]` (standalone) | Telegram chat ID |
| `sb_secret_...` | Supabase service key |
| `sb_publishable_...` | Supabase anon key |

## GitHub Secrets
If the key is needed for CI/CD (GitHub Actions), ALSO set it via:
```bash
gh secret set KEY_NAME --body "value" --repo ganbaroff/volaura
```
Confirm with: `gh secret list --repo ganbaroff/volaura`

## NEVER
- Ask CEO to add secrets manually when GitHub CLI is available
- Leave secrets unrecorded after conversation ends
- Put secrets in CLAUDE.md, DECISIONS.md, or any non-.gitignored file
