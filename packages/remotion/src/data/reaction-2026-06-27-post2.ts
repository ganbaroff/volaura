/**
 * ReactionDuet — Post #2 from weekly batch 2026-04-13 (MindShift / swarm audit).
 * Source: docs/content/weekly-plans/2026-04-13.md (row 2, DRAFT READY)
 *
 * Phase 0 stand-in assets in public/standin/ until CEO lip-sync clip lands.
 * Pipeline fills audio + captions at runtime into public/voiceovers/.
 */

import type { Caption } from "@remotion/captions";
import type { ReactionDuetProps } from "../compositions/ReactionDuet";

const captions: Caption[] | undefined = undefined;

export const reaction20260627Post2: ReactionDuetProps["data"] = {
  brandHandle: "@volaura.io",
  accentProduct: "mindshift",
  sourceImage: "standin/source-placeholder.png",
  avatarImage: "standin/avatar-placeholder.png",
  disclosure: "AI-generated · reaksiya",
  cta: {
    line: "Link in bio",
    brand: "volaura.io",
  },
  audio: undefined,
  captions,
};

/** Full AZ voice-over script (Post #2). Used by content_pipeline TTS step. */
export const reaction20260627Post2Script = [
  "44 süni intellekt agentim var.",
  "Dünən onlar 48 xəta tapdılar.",
  "Mən 3 tapmışdım.",
  "Agents audited the code — 48 mistakes.",
  "Ən pisi nədir bilirsiz? Onlar haqlı idilər.",
  "Link in bio — volaura.io",
].join("\n");
