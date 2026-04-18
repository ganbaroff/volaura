import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("@radix-ui/react-slot", () => {
  const React = require("react");
  const SlotMock = React.forwardRef(
    ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }, ref: React.Ref<HTMLElement>) => {
      if (!React.isValidElement(children)) return null;
      return React.cloneElement(children as React.ReactElement<Record<string, unknown>>, { ...props, ref });
    }
  );
  SlotMock.displayName = "SlotMock";
  return { Slot: SlotMock };
});

// ── Import after mocks ────────────────────────────────────────────────────────

import { EmptyState } from "@/components/ui/empty-state";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("EmptyState — required title", () => {
  it("renders the title text", () => {
    render(<EmptyState title="Start your first assessment" />);
    expect(screen.getByText("Start your first assessment")).toBeInTheDocument();
  });

  it("renders title as an h3 element", () => {
    render(<EmptyState title="Explore competencies" />);
    const heading = screen.getByText("Explore competencies");
    expect(heading.tagName).toBe("H3");
  });

  it("title has semibold font class", () => {
    render(<EmptyState title="My Title" />);
    expect(screen.getByText("My Title").className).toContain("font-semibold");
  });
});

describe("EmptyState — optional description", () => {
  it("renders description when provided", () => {
    render(
      <EmptyState
        title="No data"
        description="Your activity will appear here once you get started."
      />
    );
    expect(
      screen.getByText("Your activity will appear here once you get started.")
    ).toBeInTheDocument();
  });

  it("does not render description paragraph when not provided", () => {
    render(<EmptyState title="No data" />);
    // No p with muted-foreground text-sm besides title
    const paras = document.querySelectorAll("p.text-sm");
    expect(paras.length).toBe(0);
  });

  it("description has muted styling", () => {
    render(<EmptyState title="T" description="Some description text" />);
    const desc = screen.getByText("Some description text");
    expect(desc.className).toContain("text-muted-foreground");
  });
});

describe("EmptyState — optional icon", () => {
  it("renders icon when provided as emoji string", () => {
    render(<EmptyState title="Empty" icon="🎯" />);
    expect(screen.getByText("🎯")).toBeInTheDocument();
  });

  it("renders icon when provided as React node", () => {
    render(<EmptyState title="Empty" icon={<svg data-testid="icon-svg" />} />);
    expect(screen.getByTestId("icon-svg")).toBeInTheDocument();
  });

  it("icon container has aria-hidden to hide from screen readers", () => {
    render(<EmptyState title="Empty" icon="🎯" />);
    const iconContainer = screen.getByText("🎯").closest("[aria-hidden]");
    expect(iconContainer).toHaveAttribute("aria-hidden", "true");
  });

  it("does not render icon container when icon not provided", () => {
    render(<EmptyState title="Empty" />);
    expect(document.querySelector("[aria-hidden='true']")).toBeNull();
  });
});

describe("EmptyState — optional CTA button", () => {
  it("renders CTA button when both ctaLabel and onCtaClick provided", () => {
    render(
      <EmptyState
        title="Empty"
        ctaLabel="Get started"
        onCtaClick={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: "Get started" })).toBeInTheDocument();
  });

  it("calls onCtaClick when CTA button clicked", async () => {
    const user = userEvent.setup();
    const onCtaClick = vi.fn();
    render(
      <EmptyState
        title="Empty"
        ctaLabel="Take assessment"
        onCtaClick={onCtaClick}
      />
    );
    await user.click(screen.getByRole("button", { name: "Take assessment" }));
    expect(onCtaClick).toHaveBeenCalledTimes(1);
  });

  it("does not render CTA button when ctaLabel is missing", () => {
    render(<EmptyState title="Empty" onCtaClick={vi.fn()} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("does not render CTA button when onCtaClick is missing", () => {
    render(<EmptyState title="Empty" ctaLabel="Click me" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("does not render CTA button when neither ctaLabel nor onCtaClick provided", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("EmptyState — layout and className", () => {
  it("applies custom className to the container", () => {
    const { container } = render(
      <EmptyState title="Empty" className="min-h-screen" />
    );
    expect(container.firstChild).toHaveClass("min-h-screen");
  });

  it("has center alignment classes by default", () => {
    const { container } = render(<EmptyState title="Empty" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("justify-center");
  });

  it("has text-center class", () => {
    const { container } = render(<EmptyState title="Empty" />);
    expect((container.firstChild as HTMLElement).className).toContain("text-center");
  });
});

describe("EmptyState — full composition", () => {
  it("renders all parts together correctly", () => {
    const onCtaClick = vi.fn();
    render(
      <EmptyState
        title="Start your journey"
        description="Complete your first assessment to earn your AURA score."
        icon="⭐"
        ctaLabel="Begin assessment"
        onCtaClick={onCtaClick}
      />
    );

    expect(screen.getByText("Start your journey")).toBeInTheDocument();
    expect(
      screen.getByText("Complete your first assessment to earn your AURA score.")
    ).toBeInTheDocument();
    expect(screen.getByText("⭐")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Begin assessment" })).toBeInTheDocument();
  });
});
