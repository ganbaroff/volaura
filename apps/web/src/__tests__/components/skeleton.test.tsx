import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import React from "react";

// ── Import ────────────────────────────────────────────────────────────────────

import { Skeleton } from "@/components/ui/skeleton";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Skeleton — rendering", () => {
  it("renders a div element", () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("has animate-pulse class for loading effect", () => {
    const { container } = render(<Skeleton />);
    expect((container.firstChild as HTMLElement).className).toContain("animate-pulse");
  });

  it("has rounded-md class", () => {
    const { container } = render(<Skeleton />);
    expect((container.firstChild as HTMLElement).className).toContain("rounded-md");
  });

  it("has bg-muted class", () => {
    const { container } = render(<Skeleton />);
    expect((container.firstChild as HTMLElement).className).toContain("bg-muted");
  });
});

describe("Skeleton — className merging", () => {
  it("merges custom className with defaults", () => {
    const { container } = render(<Skeleton className="h-4 w-full" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("animate-pulse");
    expect(el.className).toContain("h-4");
    expect(el.className).toContain("w-full");
  });

  it("preserves default classes when custom class added", () => {
    const { container } = render(<Skeleton className="my-custom" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("bg-muted");
    expect(el.className).toContain("my-custom");
  });

  it("works without a className prop", () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("can override shape with className", () => {
    const { container } = render(<Skeleton className="rounded-full h-10 w-10" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("rounded-full");
    expect(el.className).toContain("h-10");
    expect(el.className).toContain("w-10");
  });
});

describe("Skeleton — html attributes", () => {
  it("passes additional html attributes to the div", () => {
    const { container } = render(<Skeleton data-testid="my-skeleton" />);
    expect(container.querySelector("[data-testid='my-skeleton']")).toBeInTheDocument();
  });

  it("passes aria attributes", () => {
    const { container } = render(<Skeleton aria-label="Loading content" />);
    expect(container.firstChild).toHaveAttribute("aria-label", "Loading content");
  });
});

describe("Skeleton — size variations", () => {
  it("renders correctly as a text line skeleton", () => {
    const { container } = render(<Skeleton className="h-4 w-[250px]" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("h-4");
    expect(el.className).toContain("w-[250px]");
  });

  it("renders correctly as a circle avatar skeleton", () => {
    const { container } = render(<Skeleton className="h-12 w-12 rounded-full" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("rounded-full");
    expect(el.className).toContain("h-12");
  });

  it("renders correctly as a card content skeleton", () => {
    const { container } = render(<Skeleton className="h-[200px] w-full" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("h-[200px]");
    expect(el.className).toContain("w-full");
  });
});
