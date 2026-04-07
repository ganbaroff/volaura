#!/bin/bash
# UserPromptSubmit hook — CEO trigger word enforcement.
# When CEO uses critical language → inject mandatory response template
# exit 2 = block turn | exit 0 = allow | stdout = feedback shown to Claude
#
# Trigger words: 100%, очень важно, критично, уверен ли, точно ли, проверил ли

STDIN=$(cat)
PROMPT=$(echo "$STDIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null)

TRIGGER_PATTERN="100%|очень важно|критично|уверен ли|точно ли|проверил ли|на 100|you sure|are you certain|did you check"

if echo "$PROMPT" | grep -qiE "$TRIGGER_PATTERN"; then
  echo "══════════════════════════════════════════════════════════════"
  echo "⚡ CEO CRITICAL SIGNAL DETECTED"
  echo "══════════════════════════════════════════════════════════════"
  echo ""
  echo "Before responding, your answer MUST contain these two sections:"
  echo ""
  echo "  ## Что проверено"
  echo "  [list each claim with the tool call that proved it]"
  echo ""
  echo "  ## Что НЕ проверено"
  echo "  [list open questions — честно, не скрывать]"
  echo ""
  echo "Response without both sections = invalid. Rewrite."
  echo "══════════════════════════════════════════════════════════════"
fi

exit 0
