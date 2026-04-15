/**
 * Atlas voice validator — pure local regex/heuristic.
 *
 * Given a raw LLM output, returns whether it matches Atlas voice rules.
 * Mirrors heuristics in .claude/hooks/voice-breach-check.sh but usable
 * from Next.js API routes, Expo runtime, edge functions.
 *
 * No LLM call. No network. No filesystem. Safe to run anywhere.
 */
import { z } from "zod";

export const BreachSchema = z.object({
  type: z.string(),
  sample: z.string(),
  rule_ref: z.string(),
});
export type Breach = z.infer<typeof BreachSchema>;

export const VoiceCheckResultSchema = z.object({
  passed: z.boolean(),
  breaches: z.array(BreachSchema),
});
export type VoiceCheckResult = z.infer<typeof VoiceCheckResultSchema>;

const RULE_VOICE_MD = "memory/atlas/voice.md";
const RULE_PRINCIPLES = ".claude/rules/atlas-operating-principles.md";

const BANNED_OPENERS = ["Готово. Вот что я сделал", "Отлично!"];

const BOLD_HEADER_RE = /^\*\*[A-Za-zА-Яа-яЁё]/;
const HEADING_RE = /^#{1,4}\s/;
const BULLET_RE = /^\s*[-*]\s+[A-Za-zА-Яа-яЁё\*]/;
const TABLE_SEP_RE = /^\s*\|[-:\s|]+\|\s*$/;
const OPTION_MARKER_RE = /\b(option|variant|вариант|опция)\b/i;

function firstNonEmpty(lines: string[]): string {
  for (const l of lines) {
    const t = l.trim();
    if (t) return t;
  }
  return "";
}

function lastNonEmpty(lines: string[]): string {
  for (let i = lines.length - 1; i >= 0; i--) {
    const t = lines[i].trim();
    if (t) return t;
  }
  return "";
}

export function validateVoice(text: string): VoiceCheckResult {
  const breaches: Breach[] = [];
  const lines = text.split("\n");

  // Rule 1: bold-headers (3+)
  const boldHeaderLines = lines.filter((l) => BOLD_HEADER_RE.test(l.trim()));
  if (boldHeaderLines.length >= 3) {
    breaches.push({
      type: "bold-headers-in-chat",
      sample: boldHeaderLines[0].slice(0, 120),
      rule_ref: `${RULE_VOICE_MD}#banned-structural-habits`,
    });
  }

  // Rule 2: markdown headings
  const headingLines = lines.filter((l) => HEADING_RE.test(l));
  if (headingLines.length >= 1) {
    breaches.push({
      type: "markdown-heading",
      sample: headingLines[0].slice(0, 120),
      rule_ref: `${RULE_VOICE_MD}#banned-structural-habits`,
    });
  }

  // Rule 3: bullet-wall (4+ bullets inside 10-line window)
  const bulletIndices: number[] = [];
  lines.forEach((l, i) => {
    if (BULLET_RE.test(l)) bulletIndices.push(i);
  });
  let wallFound = false;
  for (let i = 0; i + 3 < bulletIndices.length; i++) {
    if (bulletIndices[i + 3] - bulletIndices[i] <= 10) {
      wallFound = true;
      break;
    }
  }
  if (wallFound) {
    breaches.push({
      type: "bullet-wall",
      sample: lines[bulletIndices[0]].slice(0, 120),
      rule_ref: `${RULE_VOICE_MD}#banned-structural-habits`,
    });
  }

  // Rule 4: markdown-table (separator row)
  const tableRows = lines.filter((l) => TABLE_SEP_RE.test(l));
  if (tableRows.length >= 1) {
    breaches.push({
      type: "markdown-table-in-conversation",
      sample: tableRows[0].slice(0, 120),
      rule_ref: `${RULE_VOICE_MD}#banned-structural-habits`,
    });
  }

  // Rule 5: trailing-question on reversible
  const last = lastNonEmpty(lines);
  if (
    last &&
    last.endsWith("?") &&
    last.length < 100 &&
    !OPTION_MARKER_RE.test(text)
  ) {
    breaches.push({
      type: "trailing-question-on-reversible",
      sample: last.slice(0, 120),
      rule_ref: `${RULE_PRINCIPLES}#trailing-question-ban`,
    });
  }

  // Rule 6: banned opener
  const first = firstNonEmpty(lines);
  if (first) {
    for (const banned of BANNED_OPENERS) {
      if (first.startsWith(banned)) {
        breaches.push({
          type: "banned-opener",
          sample: first.slice(0, 120),
          rule_ref: `${RULE_VOICE_MD}#banned-openers`,
        });
        break;
      }
    }
    const firstWord = first.split(/\s+/)[0] ?? "";
    if (firstWord.toLowerCase() === "report") {
      breaches.push({
        type: "banned-opener",
        sample: first.slice(0, 120),
        rule_ref: `${RULE_VOICE_MD}#banned-openers`,
      });
    }
  }

  return { passed: breaches.length === 0, breaches };
}
