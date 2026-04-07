import figma from "@figma/code-connect";
import { BadgeDisplay } from "@/components/aura/badge-display";

/**
 * Code Connect: BadgeDisplay ↔ Figma "BadgeDisplay" component set
 * Figma: https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-58
 * Tiers: Platinum ≥90 · Gold ≥75 · Silver ≥60 · Bronze ≥40 · None <40
 */
figma.connect(
  BadgeDisplay,
  "https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-58",
  {
    props: {
      tier: figma.enum("tier", {
        platinum: "platinum",
        gold: "gold",
        silver: "silver",
        bronze: "bronze",
        none: "none",
      }),
    },
    example: ({ tier }) => (
      <BadgeDisplay
        tier={tier}
        label={tier.charAt(0).toUpperCase() + tier.slice(1)}
      />
    ),
  }
);
