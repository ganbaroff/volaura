/**
 * TikTok AZ — Post #2 from weekly batch 2026-04-13.
 * Source: docs/content/weekly-plans/2026-04-13.md (row 2, DRAFT READY)
 *
 * Hook type: Data
 * Duration: 45s
 * Product accent: MindShift emerald (focus theme)
 */

import type { TikTokAZProps } from "../compositions/TikTokAZ";

export const tiktokAZ20260413Post2: TikTokAZProps["data"] = {
  brandHandle: "@volaura.io",
  accentProduct: "mindshift", // emerald
  hook: {
    line1: "44 süni intellekt",
    line2: "agentim var.",
  },
  beats: [
    {
      kind: "statement",
      text: "Dünən onlar",
      highlight: "48 xəta tapdılar.",
    },
    {
      kind: "contrast",
      text: "Mən",
      highlight: "3",
      textTail: "tapmışdım.",
    },
    {
      kind: "counter",
      label: "Agents audited the code",
      from: 0,
      to: 48,
      suffix: " mistakes",
    },
    {
      kind: "punchline",
      text: "Ən pisi nədir bilirsiz?",
      highlight: "Onlar haqlı idilər.",
    },
  ],
  cta: {
    line: "Link in bio",
    brand: "volaura.io",
  },
  // Evidence list — agent names that appear on screen during audit segment
  agentNames: [
    "Security Auditor",
    "Typescript Guard",
    "UX Critic",
    "Perf Watcher",
    "I18n Inspector",
    "ADHD Advocate",
    "Constitution Checker",
    "Telemetry Lead",
    "Brand Voice",
    "Data Steward",
  ],
};
