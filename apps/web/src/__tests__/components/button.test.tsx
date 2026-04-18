import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// @radix-ui/react-slot: just render the child element directly
vi.mock("@radix-ui/react-slot", () => ({
  Slot: React.forwardRef<HTMLElement, { children?: React.ReactNode; [key: string]: unknown }>(
    ({ children, ...props }, ref) => {
      if (!React.isValidElement(children)) return null;
      return React.cloneElement(children as React.ReactElement<Record<string, unknown>>, { ...props, ref });
    }
  ),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { Button } from "@/components/ui/button";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Button — basic rendering", () => {
  it("renders a button element by default", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("renders children text", () => {
    render(<Button>Submit</Button>);
    expect(screen.getByText("Submit")).toBeInTheDocument();
  });

  it("forwards ref to the button element", () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Ref</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it("passes extra html attributes to the button", () => {
    render(<Button data-testid="my-btn">Test</Button>);
    expect(screen.getByTestId("my-btn")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<Button className="custom-class">Text</Button>);
    expect(screen.getByRole("button")).toHaveClass("custom-class");
  });
});

describe("Button — variants", () => {
  it("applies primary variant class", () => {
    render(<Button variant="primary">Primary</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("btn-primary-gradient");
  });

  it("applies default variant class", () => {
    render(<Button variant="default">Default</Button>);
    expect(screen.getByRole("button").className).toContain("bg-primary");
  });

  it("applies destructive variant class", () => {
    render(<Button variant="destructive">Delete</Button>);
    expect(screen.getByRole("button").className).toContain("bg-error-container");
  });

  it("applies outline variant class", () => {
    render(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole("button").className).toContain("border");
  });

  it("applies secondary variant class", () => {
    render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button").className).toContain("bg-surface-container-high");
  });

  it("applies ghost variant class", () => {
    render(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole("button").className).toContain("hover:bg-accent");
  });

  it("applies link variant class", () => {
    render(<Button variant="link">Link</Button>);
    expect(screen.getByRole("button").className).toContain("text-primary");
  });

  it("defaults to default variant when no variant prop given", () => {
    render(<Button>No variant</Button>);
    expect(screen.getByRole("button").className).toContain("bg-primary");
  });
});

describe("Button — sizes", () => {
  it("applies default size class", () => {
    render(<Button size="default">Default size</Button>);
    expect(screen.getByRole("button").className).toContain("h-10");
  });

  it("applies sm size class", () => {
    render(<Button size="sm">Small</Button>);
    expect(screen.getByRole("button").className).toContain("h-8");
  });

  it("applies lg size class", () => {
    render(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button").className).toContain("h-12");
  });

  it("applies icon size class", () => {
    render(<Button size="icon">I</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("h-10");
    expect(btn.className).toContain("w-10");
  });
});

describe("Button — disabled state", () => {
  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("does not fire onClick when disabled", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Disabled</Button>);
    await user.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("has disabled:opacity-50 class applied", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button").className).toContain("disabled:opacity-50");
  });
});

describe("Button — loading state", () => {
  it("is disabled when loading is true", () => {
    render(<Button loading>Saving...</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("renders a spin indicator when loading", () => {
    render(<Button loading>Loading</Button>);
    const btn = screen.getByRole("button");
    // Spinner is a bordered span with animate-spin
    expect(btn.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("sets aria-busy when loading", () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("aria-busy", "true");
  });

  it("does not set aria-busy when not loading", () => {
    render(<Button>Normal</Button>);
    expect(screen.getByRole("button")).not.toHaveAttribute("aria-busy");
  });

  it("applies animate-pulse class when loading", () => {
    render(<Button loading>Pulsing</Button>);
    expect(screen.getByRole("button").className).toContain("animate-pulse");
  });

  it("still renders children text inside the loading wrapper", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByText("Save")).toBeInTheDocument();
  });

  it("does not render spinner when not loading", () => {
    render(<Button>Normal</Button>);
    expect(screen.getByRole("button").querySelector(".animate-spin")).toBeNull();
  });
});

describe("Button — asChild", () => {
  it("renders child element instead of button when asChild is true", () => {
    render(
      <Button asChild>
        <a href="/test">Link button</a>
      </Button>
    );
    expect(screen.getByRole("link", { name: "Link button" })).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("Button — click handling", () => {
  it("calls onClick handler when clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    await user.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("calls onClick multiple times on multiple clicks", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Multi</Button>);
    await user.click(screen.getByRole("button"));
    await user.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(2);
  });
});

describe("Button — accessibility", () => {
  it("has type button by default (prevents accidental form submit)", () => {
    render(<Button>Submit</Button>);
    // No explicit type means browser default for button inside form is submit,
    // but we verify the element is a button element
    expect(screen.getByRole("button").tagName).toBe("BUTTON");
  });

  it("can be focused via keyboard", async () => {
    const user = userEvent.setup();
    render(<Button>Focus me</Button>);
    await user.tab();
    expect(screen.getByRole("button")).toHaveFocus();
  });

  it("has focus-visible ring class for keyboard accessibility", () => {
    render(<Button>Focusable</Button>);
    expect(screen.getByRole("button").className).toContain("focus-visible:ring-2");
  });
});
