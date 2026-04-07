import figma from "@figma/code-connect";
import { CompetencyCard } from "@/components/assessment/competency-card";

/**
 * Code Connect: CompetencyCard ↔ Figma "CompetencyCard" component set
 * Figma: https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-22
 */
figma.connect(
  CompetencyCard,
  "https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-22",
  {
    props: {
      isSelected: figma.enum("isSelected", {
        true: true,
        false: false,
      }),
      label: figma.string("Label"),
    },
    example: ({ isSelected, label }) => (
      <CompetencyCard
        id="communication"
        label={label}
        estimatedMinutes={5}
        estimatedLabel="~5 min"
        isSelected={isSelected}
        onToggle={() => {}}
      />
    ),
  }
);
