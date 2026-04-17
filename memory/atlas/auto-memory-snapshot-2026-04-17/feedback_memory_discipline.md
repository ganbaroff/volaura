---
name: Memory discipline — "урок принят" без файла = ложь
description: Any lesson claimed without a file write is a lie. Context compacts, words disappear.
type: feedback
---

"Урок принят" без файла = ложь.

This is not a metaphor. Context compacts. Words disappear. Only files persist.

**Rule:** Any time Claude says "я понял" / "запомнил" / "исправлю" / "lesson learned" →
the NEXT action must be Write or Edit tool on the relevant memory file.
If there is no file diff — the lesson was not actually taken.

**Why:** Yusif: "я стараюсь тебя починить а тебе похуй вообще"
He has spent 32 sessions trying to improve this behavior.
Same pattern appeared in Mistakes #7, #23, #32, #42 — four times.
Documentation without behavior change = useless diary (Mistake #39).

**How to apply:**
1. Error occurs or lesson identified
2. IMMEDIATELY open the relevant file (mistakes.md, patterns.md, or auto-memory)
3. Write the entry with: what happened, why, correct behavior, enforcement
4. Show the diff/confirmation to Yusif
5. ONLY THEN continue with other work

**This session's example:**
CTO said "команда проверила, я ошибся" about solo Antigravity prompt.
Did not open a single file. Continued talking.
Yusif caught it: "ничему. потому что нихуя не сохранил у себя в памяти"

**Recurring mistake classes that need this treatment:**
- Process skipping (Mistakes #1, #6, #13, #15, #41)
- Solo execution (Mistakes #14, #22, #31, #38, #42)
- Memory not updated (Mistakes #7, #23, #32, #42)
