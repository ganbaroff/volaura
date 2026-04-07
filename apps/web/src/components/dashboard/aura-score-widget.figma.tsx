import figma from "@figma/code-connect";
import { AuraScoreWidget } from "@/components/dashboard/aura-score-widget";

/**
 * Code Connect: AuraScoreWidget ↔ Figma "AuraScoreWidget" component set
 * Figma: https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-95
 * Identity headline first, score as context (Research #10: Overjustification)
 */
figma.connect(
  AuraScoreWidget,
  "https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-95",
  {
    props: {
      badgeTier: figma.enum("badgeTier", {
        platinum: "platinum",
        gold: "gold",
        silver: "silver",
        bronze: "bronze",
        none: "none",
      }),
    },
    example: ({ badgeTier }) => (
      <AuraScoreWidget
        score={badgeTier === "platinum" ? 9.2 : badgeTier === "gold" ? 7.8 : badgeTier === "silver" ? 5.4 : badgeTier === "bronze" ? 3.2 : 0}
        badgeTier={badgeTier}
        isElite={false}
        locale="en"
      />
    ),
  }
);
