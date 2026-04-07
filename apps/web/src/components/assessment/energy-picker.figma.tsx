import figma from "@figma/code-connect";
import { EnergyPicker, type EnergyLevel } from "@/components/assessment/energy-picker";

/**
 * Code Connect: EnergyPicker ↔ Figma "EnergyPicker" component set
 * Figma: https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-36
 * Constitution Law 2: Energy Adaptation — every product needs Full/Mid/Low energy modes
 */
figma.connect(
  EnergyPicker,
  "https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-36",
  {
    props: {
      value: figma.enum("value", {
        full: "full" as EnergyLevel,
        mid: "mid" as EnergyLevel,
        low: "low" as EnergyLevel,
      }),
    },
    example: ({ value }) => (
      <EnergyPicker value={value} onChange={() => {}} />
    ),
  }
);
