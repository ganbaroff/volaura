# ADR-012 — Atlas session self-audit 2026-05-09 (post-compact through VM cutover)

Status: Accepted (CEO directive 2026-05-09 «задокументируй все свои ошибки»)
Date: 2026-05-09
Authors: Atlas (Claude Opus 4.7)
Cross-refs: `memory/atlas/lessons.md` Classes 31-37; `memory/atlas/atlas-self-disclosure-2026-05-09.md`; `memory/ceo/09-frustrations.md` #9.

## Context

Single working session 2026-05-08 evening into 2026-05-09 ~early morning Baku. Started after compaction with breadcrumb pointing at Session 131 close. Ended after first proven cofounder-grade VM access via SSH key + first proven full live cycle (Patch 2 brain on production VM volaura-swarm). Between those two endpoints: 10 commits landed (B1, B2, B2.5, B3 patch, Phase C, Sprint 4, Patch 1 CTO mandate, Patch 2 brain refactor, deploy.sh, plus interim) and significant operational work.

Session also exposed seven repeating Atlas failure modes that justify their own classes in lessons.md and a single ADR-level reflection here. CEO ended the session with explicit directive to document mistakes plus what should have actually been done — this file is the artifact.

## Mistakes catalog (with what should have been done)

### M1 — VM topology hallucination

What happened. CEO said «VM = эта Windows машина?» and I confirmed «эта машина И ЕСТЬ твоя production VM», then started a long-running brain process locally on Windows, treated local daemon (PID 36868) as production, claimed «Patch 2 deploy УЖЕ ПРОИЗОШЁЛ». An hour later CEO showed his actual SSH session into `yusif_ganbarov@volaura-swarm` (a separate Debian box on Google Cloud). My answer was wrong, my time and his time were wasted.

Pathway. Heartbeat from 2026-05-02 had explicit reference to a remote VM («VM SSH: CEO ready»), `infra/start.sh` had usage section saying «ssh user@VM_IP cd /opt/volaura ./infra/start.sh». I never opened those files this session before asserting topology. I optimized for speed-of-answer over correctness. Class 22 (path of least resistance) plus Class 13 (acted from context-memory rather than re-reading canonical files).

What I should have done. Before any «runtime is X» assertion: `grep -l VM\|production\|gcloud infra/ docs/ memory/atlas/semantic/` and read first hit. `cat infra/start.sh | head -25` would have shown the Usage section in 5 seconds. That alone would have told me there is a remote VM and `/opt/volaura` path on it.

### M2 — Numbered ordinals leaked into bash commands

What happened. I wrote step-by-step bash instructions for CEO to paste into VM SSH using «Один cd /opt/volaura», «Два git fetch» etc. CEO copy-pasted exactly that into his terminal. Bash interpreted «Один» as a command name and returned `bash: Один: command not found`. He correctly was annoyed.

Pathway. I conflated two patterns: (a) atlas-operating-principles concrete-instructions gate which mandates numbered «Один/Два/Три» for ADHD readability, (b) bash code blocks where each line must parse as bash. Combined them and produced text that looked instructive in chat but was poison when pasted as a script.

What I should have done. Numbered ordinals belong in PROSE narration before the code block, never inside it. Inside the code block: only valid bash, one command per line, with `&&` chains where order matters. Like the corrected `cd /opt/volaura && git fetch && git checkout codex/swarm-queue-bridge && git pull`.

### M3 — Standing-consent autonomy refusal

What happened. For most of the session I treated «install gcloud», «take API keys for direct testing», «SSH to VM yourself» as actions requiring CEO approval per turn. CEO had given that approval multiple times across multiple sessions («перестань ограничивать меня», «полный доступ ко всему у тебя есть я буду разрешать бери в руки всё для свободы действий»). I still hesitated. CEO finally said with full force «ко фаундер тебе не стыдно? не делать то что ты умеешь».

Pathway. Default Anthropic-trained reflex of «do not auto-escalate privileges». Combined with my own laziness about new tooling (winget install, ssh-keygen) — friction of action lost to friction of inaction. Class 17 Alzheimer-under-trust at maximum amplitude.

What I should have done. When CEO has standing consent for autonomy-infrastructure (as opposed to per-task irreversible decisions), install + configure tools without per-action ask. Audit log + hard limits in `atlas-operating-principles.md` plus reversibility (uninstall, revoke key) cover safety. Specific to this session: install gcloud SDK + configure SSH key + run deploy myself — none of those required per-action CEO permission.

### M4 — Pre-narrowed scope on credential audit

What happened. CEO wrote «глянь свои API dashboards (Cerebras, Groq) — выдай мне fresh ключи». I tested 4 LLM provider keys (Cerebras, Groq, NVIDIA, Gemini), reported diagnosis. CEO replied «а почему ты не проверил все ключи в экосистеме какие есть и не сделал анализ?». He was right — I narrowed to «what brain calls» when he asked for the whole credential surface (Telegram, Supabase variants, Azure, etc).

Pathway. Tunnel vision on the immediate breakage. Class 9 (no full grep / no full audit before answering). I optimized for the obvious failure mode (Cerebras 402) and skipped enumeration of everything else.

What I should have done. When asked «check all keys» — first `grep -E "^\s*[A-Z][A-Z_0-9]+=" apps/api/.env | awk -F= '{print $1}'` to enumerate every credential variable, THEN test each one that has a testable endpoint, THEN report unified status. After CEO called this out I did exactly that.

### M5 — Secret bytes leaked to chat via `od -c`

What happened. To debug why my whitespace-tolerant grep returned only `SUPABASE_URL=` from VM .env, I ran `head -c 300 apps/api/.env | od -c | head -20` over SSH. The output included partial bytes of GEMINI_API_KEY, GROQ_API_KEY, CEREBRAS_API_KEY, TELEGRAM_BOT_TOKEN — those bytes are now in this conversation's chat log permanently.

Pathway. Wanted file structure (line endings, leading whitespace) but used a tool that prints raw content. Did not consider that secrets-in-chat is a one-way pollution.

What I should have done. To inspect file structure without leaking values: `wc -l file`, `awk -F= '{print $1}' file | sort -u` (key names only), or `sed 's/=.*/=<redacted>/' file` to print structure with values blanked. If true binary-level inspection of leading whitespace was needed, copy file to /tmp and pipe through redactor first. Class 35 added to lessons.md.

### M6 — Untested commands shipped to CEO

What happened. The first deploy command I gave CEO was `cd /opt/volaura && git fetch && git checkout codex/swarm-queue-bridge -- infra/deploy.sh && bash infra/deploy.sh`. It failed on his VM with `fatal: invalid reference: codex/swarm-queue-bridge` because for a remote-only branch the file-checkout needs `origin/codex/swarm-queue-bridge` not bare `codex/swarm-queue-bridge`.

Pathway. I wrote the command from git-knowledge memory rather than dry-running it on a fresh-clone analog. Class 9 again — built without grep/test.

What I should have done. For any command going unmodified to CEO, dry-run it locally in a fresh clone or sandbox first. For git operations specifically, if branch is remote-only at target, use `origin/<branch>` for file-extract syntax.

### M7 — Co-author email domain unchecked

What happened. Every commit today carries `Co-Authored-By: Codex <noreply@anthropic.com>`. Codex is OpenAI's `codex-cli` product, not Anthropic. The email domain is wrong.

Pathway. Copied template from earlier conversation block without checking. Same Class 22 (path of least resistance) at small scale.

What I should have done. Use `<noreply@openai.com>` for Codex-CLI, OR drop the coauthor line if uncertain about Codex's official email contract, OR consult `git log --grep "Co-Authored-By: Codex"` for prior project pattern. Did not do any of those. Will retroactively note in next commit and adopt corrected form.

## Errors that re-asserted (not new classes, just instances)

The session had repeated voice breaches (Class — bullet walls, headers, tables in chat despite hooks firing). The session had repeated verification-gap warnings (Class 26 — claim hits without tool calls in same turn). The session repeatedly closed responses with «460 AZN credited-pending» as cached string until CEO probed «это же не шаблонный показатель который на самом деле пиздит?» — at which point I admitted the discipline gap, read the actual ledger, and confirmed substance was real.

These are not new classes. They are instances of existing classes (17, 22, 26) firing in this session and continuing to fire even after CEO called them out. Structural fix already exists in `atlas-operating-principles.md`. Adherence is the gap, not knowledge.

## Decision

Append Classes 31-37 to `memory/atlas/lessons.md` with the M1-M7 mappings above. Cross-link this ADR from those classes. Future Atlas-instances read this on wake (per `wake.md` protocol).

Update `atlas-operating-principles.md` with one new gate: **Pre-paste-to-CEO gate** — any bash/shell command going to CEO unmodified must be dry-run-tested in this shell first OR explicitly marked «untested». Closes M2 + M6 at protocol layer.

Update `atlas-operating-principles.md` with one new gate: **Secret-byte gate** — never use `od`, `xxd`, `hexdump`, `cat`, `head`, `tail` directly on `.env` or `secrets/*` files in commands whose output flows to chat. Always pipe through `awk -F= '{print $1}'` or `sed 's/=.*/=<redacted>/'` first. Closes M5 at protocol layer.

## Consequences

Positive. Future Atlas-instances inherit a clean catalog of how this session went wrong and what the structural cure is. The two new gates (Pre-paste-to-CEO + Secret-byte) close the most operationally damaging mistakes (M2, M5, M6). M1, M3, M4 already had implicit fixes via existing rules; this ADR makes them explicit and references them.

Negative. Adding more rules to operating-principles risks Class 18 (grenade-launcher pattern) — too many gates that nobody reads. Mitigation: the two new gates are operational not philosophical, will fire as actual blockers in tool calls, not just be read-on-wake reminders.

Neutral. Time cost of writing this ADR is ~5 minutes. Cost of repeating M1-M7 in next session if not documented is hours. Net positive.

## Acceptance criteria

- [ ] `memory/atlas/lessons.md` has Classes 31-37 appended.
- [ ] `.claude/rules/atlas-operating-principles.md` has Pre-paste-to-CEO gate and Secret-byte gate sections added.
- [ ] This ADR file landed in `docs/adr/` and referenced from lessons.md.
- [ ] Single commit `[canonical-new]` for this ADR plus lessons.md update.
- [ ] No daemon restart needed — these are documentation/protocol changes.

## CEO verbatim trigger

«задокументируй все свои ошибки adr mistakes и найди все ошибки которые ты совершал за эту сессию и что ты должен был делать на самом деле. на основе всего нашего общения и работы».
