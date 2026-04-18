import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Import ────────────────────────────────────────────────────────────────────

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Card — basic rendering", () => {
  it("renders a div element", () => {
    const { container } = render(<Card>Content</Card>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("renders children", () => {
    render(<Card>Card body</Card>);
    expect(screen.getByText("Card body")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<Card className="custom">Text</Card>);
    expect(container.firstChild).toHaveClass("custom");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLDivElement>();
    render(<Card ref={ref}>Ref</Card>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("passes extra html attributes", () => {
    render(<Card data-testid="card-root">Test</Card>);
    expect(screen.getByTestId("card-root")).toBeInTheDocument();
  });
});

describe("Card — variants", () => {
  it("applies default variant classes", () => {
    const { container } = render(<Card variant="default">Default</Card>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("bg-card");
    expect(el.className).toContain("border");
  });

  it("applies elevated variant classes", () => {
    const { container } = render(<Card variant="elevated">Elevated</Card>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("bg-card");
    expect(el.className).toContain("shadow-md");
  });

  it("applies glass variant class", () => {
    const { container } = render(<Card variant="glass">Glass</Card>);
    expect((container.firstChild as HTMLElement).className).toContain("liquid-glass");
  });

  it("defaults to default variant", () => {
    const { container } = render(<Card>No variant</Card>);
    expect((container.firstChild as HTMLElement).className).toContain("bg-card");
  });

  it("always has rounded-2xl class", () => {
    const { container } = render(<Card>Rounded</Card>);
    expect((container.firstChild as HTMLElement).className).toContain("rounded-2xl");
  });
});

describe("CardHeader", () => {
  it("renders a div element", () => {
    const { container } = render(<CardHeader>Header</CardHeader>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("renders children", () => {
    render(<CardHeader>Header content</CardHeader>);
    expect(screen.getByText("Header content")).toBeInTheDocument();
  });

  it("has flex layout classes", () => {
    const { container } = render(<CardHeader>H</CardHeader>);
    expect((container.firstChild as HTMLElement).className).toContain("flex");
    expect((container.firstChild as HTMLElement).className).toContain("flex-col");
  });

  it("applies custom className", () => {
    const { container } = render(<CardHeader className="extra">H</CardHeader>);
    expect(container.firstChild).toHaveClass("extra");
  });
});

describe("CardTitle", () => {
  it("renders an h3 element", () => {
    const { container } = render(<CardTitle>Title</CardTitle>);
    expect(container.firstChild?.nodeName).toBe("H3");
  });

  it("renders children text", () => {
    render(<CardTitle>My Card Title</CardTitle>);
    expect(screen.getByText("My Card Title")).toBeInTheDocument();
  });

  it("has semibold font class", () => {
    const { container } = render(<CardTitle>T</CardTitle>);
    expect((container.firstChild as HTMLElement).className).toContain("font-semibold");
  });

  it("applies custom className", () => {
    const { container } = render(<CardTitle className="big">T</CardTitle>);
    expect(container.firstChild).toHaveClass("big");
  });
});

describe("CardDescription", () => {
  it("renders a p element", () => {
    const { container } = render(<CardDescription>Desc</CardDescription>);
    expect(container.firstChild?.nodeName).toBe("P");
  });

  it("renders children text", () => {
    render(<CardDescription>Helpful description</CardDescription>);
    expect(screen.getByText("Helpful description")).toBeInTheDocument();
  });

  it("has muted-foreground color class", () => {
    const { container } = render(<CardDescription>D</CardDescription>);
    expect((container.firstChild as HTMLElement).className).toContain("text-muted-foreground");
  });

  it("has text-sm class", () => {
    const { container } = render(<CardDescription>D</CardDescription>);
    expect((container.firstChild as HTMLElement).className).toContain("text-sm");
  });
});

describe("CardContent", () => {
  it("renders a div element", () => {
    const { container } = render(<CardContent>Body</CardContent>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("renders children", () => {
    render(<CardContent>Main content area</CardContent>);
    expect(screen.getByText("Main content area")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<CardContent className="mt-4">C</CardContent>);
    expect(container.firstChild).toHaveClass("mt-4");
  });
});

describe("CardFooter", () => {
  it("renders a div element", () => {
    const { container } = render(<CardFooter>Footer</CardFooter>);
    expect(container.firstChild?.nodeName).toBe("DIV");
  });

  it("renders children", () => {
    render(<CardFooter>Footer actions</CardFooter>);
    expect(screen.getByText("Footer actions")).toBeInTheDocument();
  });

  it("has flex and items-center layout classes", () => {
    const { container } = render(<CardFooter>F</CardFooter>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("flex");
    expect(el.className).toContain("items-center");
  });

  it("applies custom className", () => {
    const { container } = render(<CardFooter className="justify-end">F</CardFooter>);
    expect(container.firstChild).toHaveClass("justify-end");
  });
});

describe("Card — full composition", () => {
  it("renders all sub-components together correctly", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your public information</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content goes here</p>
        </CardContent>
        <CardFooter>
          <button>Save</button>
        </CardFooter>
      </Card>
    );

    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Your public information")).toBeInTheDocument();
    expect(screen.getByText("Content goes here")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });
});
