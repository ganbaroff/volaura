/**
 * LinkedIn Carousel — Post #6 from weekly batch 2026-04-13.
 * Source: docs/content/weekly-plans/2026-04-13.md (row 6)
 *
 * Hook type: Data
 * 8 slides × 3s each = 24s total
 * Each slide rendered separately as PNG for LinkedIn PDF-carousel upload,
 * or stitched as single MP4 preview.
 */

import type { LinkedInCarouselProps } from "../compositions/LinkedInCarousel";

export const carouselData20260413: LinkedInCarouselProps["data"] = {
  brand: "VOLAURA",
  title: "I gave AI full control of my startup",
  subtitle: "Here's what 44 agents actually do (and what they don't)",
  slides: [
    {
      kind: "headline",
      eyebrow: "The setup",
      body: "44 AI agents, each a skill file, each an opinion. One human founder.",
    },
    {
      kind: "stat",
      value: "44",
      label: "AI agents currently running",
      footnote: "Swarm, memory, audit, content, infra, brand — all separate perspectives.",
    },
    {
      kind: "stat",
      value: "48",
      label: "defects found in self-audit",
      footnote: "Mine: 3. Theirs: 48. They were right.",
    },
    {
      kind: "stat",
      value: "17",
      label: "deploys vetoed by Security Agent",
      footnote: "14 of those vetoes were correct. I learned to listen.",
    },
    {
      kind: "list",
      eyebrow: "What AI is good at",
      items: [
        "Finding code smells I'd normalized",
        "Disagreeing with each other — forcing the real argument",
        "Not getting tired at 2am",
        "Holding 44 perspectives I couldn't hold alone",
      ],
    },
    {
      kind: "list",
      eyebrow: "What AI is bad at",
      items: [
        "Knowing when to ship",
        "Reading the room in a sales call",
        "Taste",
        "Choosing what not to build",
      ],
    },
    {
      kind: "quote",
      body: "The question isn't whether AI can replace your team. It's whether you'd listen if it could.",
      attribution: "— me, after 17 vetoes",
    },
    {
      kind: "cta",
      headline: "Watch the full story →",
      body: "Link in the first comment. Built with 44 agents and one human.",
      handle: "volaura.io",
    },
  ],
};
