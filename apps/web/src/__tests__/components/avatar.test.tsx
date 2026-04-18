import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Import ────────────────────────────────────────────────────────────────────

import { Avatar } from "@/components/ui/avatar";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Avatar — accessibility", () => {
  it("has role img", () => {
    render(<Avatar name="John Doe" />);
    expect(screen.getByRole("img")).toBeInTheDocument();
  });

  it("has aria-label set to the user name", () => {
    render(<Avatar name="John Doe" />);
    expect(screen.getByRole("img")).toHaveAttribute("aria-label", "John Doe");
  });

  it("uses name as aria-label for screen reader identification", () => {
    render(<Avatar name="Yusif Ganbarov" />);
    expect(screen.getByRole("img", { name: "Yusif Ganbarov" })).toBeInTheDocument();
  });
});

describe("Avatar — initials fallback", () => {
  it("shows two initials from first and last name", () => {
    render(<Avatar name="John Doe" />);
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("shows single initial for single-word name", () => {
    render(<Avatar name="Atlas" />);
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("shows uppercased initials", () => {
    render(<Avatar name="john doe" />);
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("shows at most two initials for multi-word name", () => {
    render(<Avatar name="John Michael Doe" />);
    // Only first two parts
    expect(screen.getByText("JM")).toBeInTheDocument();
  });

  it("initials span has aria-hidden to prevent duplicate reading", () => {
    render(<Avatar name="John Doe" />);
    const initialsSpan = screen.getByText("JD");
    expect(initialsSpan).toHaveAttribute("aria-hidden", "true");
  });

  it("does not render img element when no src provided", () => {
    render(<Avatar name="John Doe" />);
    expect(screen.queryByRole("img", { name: /img/i })).not.toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
  });
});

describe("Avatar — image rendering", () => {
  it("renders img when src is provided", () => {
    render(<Avatar name="John Doe" src="https://example.com/avatar.jpg" />);
    const img = document.querySelector("img");
    expect(img).toBeInTheDocument();
  });

  it("img has correct src", () => {
    render(<Avatar name="John Doe" src="https://example.com/avatar.jpg" />);
    expect(document.querySelector("img")).toHaveAttribute(
      "src",
      "https://example.com/avatar.jpg"
    );
  });

  it("img has alt text matching the user name", () => {
    render(<Avatar name="John Doe" src="https://example.com/avatar.jpg" />);
    expect(document.querySelector("img")).toHaveAttribute("alt", "John Doe");
  });

  it("img has lazy loading attribute", () => {
    render(<Avatar name="John Doe" src="https://example.com/avatar.jpg" />);
    expect(document.querySelector("img")).toHaveAttribute("loading", "lazy");
  });

  it("does not render initials when src is provided", () => {
    render(<Avatar name="John Doe" src="https://example.com/avatar.jpg" />);
    expect(screen.queryByText("JD")).not.toBeInTheDocument();
  });

  it("falls back to initials when src is null", () => {
    render(<Avatar name="John Doe" src={null} />);
    expect(screen.getByText("JD")).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
  });

  it("falls back to initials when src is undefined", () => {
    render(<Avatar name="Jane Smith" />);
    expect(screen.getByText("JS")).toBeInTheDocument();
  });
});

describe("Avatar — sizes", () => {
  it("applies sm size class", () => {
    render(<Avatar name="JD" size="sm" />);
    expect(screen.getByRole("img").className).toContain("h-8");
    expect(screen.getByRole("img").className).toContain("w-8");
  });

  it("applies md size class (default)", () => {
    render(<Avatar name="JD" size="md" />);
    const el = screen.getByRole("img");
    expect(el.className).toContain("h-10");
    expect(el.className).toContain("w-10");
  });

  it("applies lg size class", () => {
    render(<Avatar name="JD" size="lg" />);
    const el = screen.getByRole("img");
    expect(el.className).toContain("h-14");
    expect(el.className).toContain("w-14");
  });

  it("applies xl size class", () => {
    render(<Avatar name="JD" size="xl" />);
    const el = screen.getByRole("img");
    expect(el.className).toContain("h-20");
    expect(el.className).toContain("w-20");
  });

  it("defaults to md when size not specified", () => {
    render(<Avatar name="JD" />);
    expect(screen.getByRole("img").className).toContain("h-10");
  });
});

describe("Avatar — badge tier glow effects", () => {
  it("applies platinum tier classes", () => {
    render(<Avatar name="JD" tier="platinum" />);
    expect(screen.getByRole("img").className).toContain("badge-glow-platinum");
  });

  it("renders platinum particle elements", () => {
    const { container } = render(<Avatar name="JD" tier="platinum" />);
    // Platinum adds 3 animated spans
    const particles = container.querySelectorAll(".animate-float, .animate-float-delayed, .animate-float-more-delayed");
    expect(particles.length).toBe(3);
  });

  it("applies gold tier classes", () => {
    render(<Avatar name="JD" tier="gold" />);
    expect(screen.getByRole("img").className).toContain("badge-glow-gold");
  });

  it("applies silver tier classes", () => {
    render(<Avatar name="JD" tier="silver" />);
    expect(screen.getByRole("img").className).toContain("badge-glow-silver");
  });

  it("applies bronze tier ring class", () => {
    render(<Avatar name="JD" tier="bronze" />);
    expect(screen.getByRole("img").className).toContain("ring-aura-bronze");
  });

  it("applies no glow for none tier", () => {
    render(<Avatar name="JD" tier="none" />);
    const el = screen.getByRole("img");
    expect(el.className).not.toContain("badge-glow");
    expect(el.className).not.toContain("ring-aura");
  });

  it("defaults to none tier when not specified", () => {
    render(<Avatar name="JD" />);
    const el = screen.getByRole("img");
    expect(el.className).not.toContain("badge-glow");
  });

  it("does not render particles for non-platinum tiers", () => {
    const { container } = render(<Avatar name="JD" tier="gold" />);
    expect(container.querySelector(".animate-float")).toBeNull();
  });
});

describe("Avatar — custom className", () => {
  it("applies custom className to the container", () => {
    render(<Avatar name="JD" className="border-2" />);
    expect(screen.getByRole("img").className).toContain("border-2");
  });

  it("preserves default classes when custom className added", () => {
    render(<Avatar name="JD" className="custom" />);
    const el = screen.getByRole("img");
    expect(el.className).toContain("rounded-full");
    expect(el.className).toContain("custom");
  });
});
