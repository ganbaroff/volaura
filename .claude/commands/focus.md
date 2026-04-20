---
description: Toggle focus mode — hides intermediate tool calls, shows only final output. Use when you trust the model and just want the result.
---

When this command is invoked:

- Suppress narration of intermediate tool calls, bash outputs, and file reads from visible response text
- Show only the final result, summary, and any blocking questions
- Announce once: "Focus mode ON — showing final results only"
- If invoked again (second `/focus`), toggle off and announce "Focus mode OFF"

This is Boris Cherny tip #4: "I generally trust it to run the right commands and make the right edits. I just look at the final result."

Toggle: Shift+Tab in CLI cycles Ask → Plan → Auto mode; `/focus` controls output verbosity separately.
