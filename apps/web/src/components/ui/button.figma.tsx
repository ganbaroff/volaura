import figma from "@figma/code-connect";
import { Button } from "@/components/ui/button";

/**
 * Code Connect: Button ↔ Figma "Button" component set
 * Figma: https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-13
 */
figma.connect(
  Button,
  "https://www.figma.com/design/B30q4nqVq5VjdqAVVYRh3t?node-id=34-13",
  {
    props: {
      variant: figma.enum("variant", {
        default: "default",
        outline: "outline",
        ghost: "ghost",
      }),
      size: figma.enum("size", {
        default: "default",
        sm: "sm",
        lg: "lg",
      }),
      label: figma.string("Label"),
    },
    example: ({ variant, size, label }) => (
      <Button variant={variant} size={size}>
        {label}
      </Button>
    ),
  }
);
