import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils/cn";

/**
 * Button System — VOLAURA Design System
 *
 * Constitution:
 * - Law 1: "destructive" uses purple (--color-error), not red
 * - Law 4: transition-duration uses --duration-fast (150ms)
 * - Law 5: Use variant="primary" for the ONE primary CTA per screen
 *
 * ADHD: All sizes meet energy-target minimum. Immediate visual feedback.
 */

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?:
    | "primary"
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link"
    | "product";
  size?: "default" | "sm" | "lg" | "icon";
  /** Loading state — shows pulse animation, disables click */
  loading?: boolean;
}

const variantClasses: Record<string, string> = {
  primary:
    "btn-primary-gradient font-semibold shadow-md hover:shadow-lg",
  default:
    "bg-primary text-on-primary hover:bg-primary/90",
  destructive:
    "bg-error-container text-on-error-container hover:bg-error-container/90",
  outline:
    "border border-border bg-transparent hover:bg-accent hover:text-accent-foreground",
  secondary:
    "bg-surface-container-high text-on-surface hover:bg-surface-container-highest",
  ghost:
    "hover:bg-accent hover:text-accent-foreground",
  link:
    "text-primary underline-offset-4 hover:underline",
  product:
    "text-surface font-semibold",
};

const sizeClasses: Record<string, string> = {
  default: "h-10 px-4 py-2 rounded-xl energy-target",
  sm: "h-8 px-3 text-xs rounded-lg",
  lg: "h-12 px-8 text-base rounded-xl energy-target",
  icon: "h-10 w-10 rounded-xl energy-target",
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "default",
      asChild = false,
      loading = false,
      disabled,
      children,
      style,
      ...props
    },
    ref,
  ) => {
    const Comp = asChild ? Slot : "button";
    const isDisabled = disabled || loading;

    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium",
          "ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          "transition-all",
          variantClasses[variant],
          sizeClasses[size],
          loading && "animate-pulse",
          className,
        )}
        ref={ref}
        disabled={isDisabled}
        aria-busy={loading || undefined}
        style={{
          transitionDuration: "var(--duration-fast)",
          ...(variant === "product"
            ? { backgroundColor: "var(--color-product-accent)" }
            : {}),
          ...style,
        } as React.CSSProperties}
        {...props}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
            <span>{children}</span>
          </span>
        ) : (
          children
        )}
      </Comp>
    );
  },
);
Button.displayName = "Button";

export { Button };
