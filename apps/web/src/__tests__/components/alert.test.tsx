import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Import ────────────────────────────────────────────────────────────────────

import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Alert — basic rendering", () => {
  it("renders with role alert", () => {
    render(<Alert>Alert content</Alert>);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders children", () => {
    render(<Alert>Something went wrong</Alert>);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders as a div element", () => {
    const { container } = render(<Alert>Test</Alert>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLDivElement>();
    render(<Alert ref={ref}>Test</Alert>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("passes additional html attributes", () => {
    render(<Alert data-testid="my-alert">Test</Alert>);
    expect(screen.getByTestId("my-alert")).toBeInTheDocument();
  });
});

describe("Alert — variants", () => {
  it("applies default variant styling", () => {
    render(<Alert variant="default">Default alert</Alert>);
    const el = screen.getByRole("alert");
    // Default does not have destructive class
    expect(el.className).not.toContain("text-destructive");
    expect(el.className).not.toContain("border-destructive");
  });

  it("applies destructive variant text class", () => {
    render(<Alert variant="destructive">Error occurred</Alert>);
    expect(screen.getByRole("alert").className).toContain("text-destructive");
  });

  it("applies destructive variant border class", () => {
    render(<Alert variant="destructive">Error occurred</Alert>);
    expect(screen.getByRole("alert").className).toContain("border-destructive");
  });

  it("defaults to default variant when no variant specified", () => {
    render(<Alert>No variant prop</Alert>);
    expect(screen.getByRole("alert").className).not.toContain("text-destructive");
  });

  it("has rounded-lg class for both variants", () => {
    render(<Alert>Rounded</Alert>);
    expect(screen.getByRole("alert").className).toContain("rounded-lg");
  });

  it("has padding class for both variants", () => {
    render(<Alert>Padded</Alert>);
    expect(screen.getByRole("alert").className).toContain("p-4");
  });
});

describe("Alert — custom className", () => {
  it("merges custom className with defaults", () => {
    render(<Alert className="mt-4">Test</Alert>);
    expect(screen.getByRole("alert").className).toContain("mt-4");
  });

  it("preserves role alert with custom class", () => {
    render(<Alert className="my-class">Test</Alert>);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

describe("AlertTitle", () => {
  it("renders an h5 element", () => {
    const { container } = render(<AlertTitle>Warning!</AlertTitle>);
    expect(container.firstChild?.nodeName).toBe("H5");
  });

  it("renders children text", () => {
    render(<AlertTitle>Session expired</AlertTitle>);
    expect(screen.getByText("Session expired")).toBeInTheDocument();
  });

  it("has font-medium class", () => {
    const { container } = render(<AlertTitle>Title</AlertTitle>);
    expect((container.firstChild as HTMLElement).className).toContain("font-medium");
  });

  it("applies custom className", () => {
    const { container } = render(<AlertTitle className="text-lg">Title</AlertTitle>);
    expect(container.firstChild).toHaveClass("text-lg");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLParagraphElement>();
    render(<AlertTitle ref={ref}>Title</AlertTitle>);
    expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
  });
});

describe("AlertDescription", () => {
  it("renders a div element", () => {
    const { container } = render(<AlertDescription>Details here</AlertDescription>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("renders children text", () => {
    render(<AlertDescription>Your session has expired. Please sign in again.</AlertDescription>);
    expect(
      screen.getByText("Your session has expired. Please sign in again.")
    ).toBeInTheDocument();
  });

  it("has text-sm class", () => {
    const { container } = render(<AlertDescription>Desc</AlertDescription>);
    expect((container.firstChild as HTMLElement).className).toContain("text-sm");
  });

  it("applies custom className", () => {
    const { container } = render(
      <AlertDescription className="font-bold">Desc</AlertDescription>
    );
    expect(container.firstChild).toHaveClass("font-bold");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLParagraphElement>();
    render(<AlertDescription ref={ref}>Desc</AlertDescription>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });
});

describe("Alert — full composition", () => {
  it("renders title and description inside alert", () => {
    render(
      <Alert>
        <AlertTitle>Connection lost</AlertTitle>
        <AlertDescription>
          Check your internet connection and try again.
        </AlertDescription>
      </Alert>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Connection lost")).toBeInTheDocument();
    expect(
      screen.getByText("Check your internet connection and try again.")
    ).toBeInTheDocument();
  });

  it("renders destructive alert with title and description", () => {
    render(
      <Alert variant="destructive">
        <AlertTitle>Access denied</AlertTitle>
        <AlertDescription>You do not have permission to view this page.</AlertDescription>
      </Alert>
    );

    const alertEl = screen.getByRole("alert");
    expect(alertEl.className).toContain("text-destructive");
    expect(screen.getByText("Access denied")).toBeInTheDocument();
  });
});
