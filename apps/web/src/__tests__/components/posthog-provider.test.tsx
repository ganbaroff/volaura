import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import React from "react";

// ── Hoisted mocks ─────────────────────────────────────────────────────────────

const { mockPosthogInit, mockPosthog, mockPHProvider } = vi.hoisted(() => {
  const mockPosthogInit = vi.fn();
  const mockPosthog = { init: mockPosthogInit };
  const mockPHProvider = vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="ph-provider">{children}</div>
  ));
  return { mockPosthogInit, mockPosthog, mockPHProvider };
});

vi.mock("posthog-js", () => ({
  default: mockPosthog,
}));

vi.mock("posthog-js/react", () => ({
  PostHogProvider: (props: { children: React.ReactNode; client: unknown }) =>
    mockPHProvider(props),
}));

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("PostHogProvider — no key (dynamic import)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_KEY", "");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_HOST", "");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("renders children directly without PHProvider wrapper", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child content</div>
      </PostHogProvider>
    );
    expect(screen.getByText("child content")).toBeInTheDocument();
    expect(screen.queryByTestId("ph-provider")).not.toBeInTheDocument();
  });

  it("does not call posthog.init when key is missing", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child</div>
      </PostHogProvider>
    );
    act(() => {});
    expect(mockPosthogInit).not.toHaveBeenCalled();
  });
});

describe("PostHogProvider — with key (dynamic import)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_KEY", "phc_testkey123");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_HOST", "");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("wraps children in PHProvider when key exists", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child content</div>
      </PostHogProvider>
    );
    expect(screen.getByTestId("ph-provider")).toBeInTheDocument();
    expect(screen.getByText("child content")).toBeInTheDocument();
  });

  it("calls posthog.init with correct config when key exists", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child</div>
      </PostHogProvider>
    );
    act(() => {});
    expect(mockPosthogInit).toHaveBeenCalledWith(
      "phc_testkey123",
      expect.objectContaining({
        capture_pageview: true,
        capture_pageleave: true,
        persistence: "localStorage+cookie",
        respect_dnt: true,
      })
    );
  });

  it("uses default host https://us.i.posthog.com when env not set", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child</div>
      </PostHogProvider>
    );
    act(() => {});
    expect(mockPosthogInit).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        api_host: "https://us.i.posthog.com",
      })
    );
  });

  it("has respect_dnt set to true", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child</div>
      </PostHogProvider>
    );
    act(() => {});
    const callArgs = mockPosthogInit.mock.calls[0];
    expect(callArgs[1].respect_dnt).toBe(true);
  });

  it("has persistence set to localStorage+cookie", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child</div>
      </PostHogProvider>
    );
    act(() => {});
    const callArgs = mockPosthogInit.mock.calls[0];
    expect(callArgs[1].persistence).toBe("localStorage+cookie");
  });
});

describe("PostHogProvider — custom host (dynamic import)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_KEY", "phc_testkey123");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_HOST", "https://custom.posthog.example.com");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses custom host when NEXT_PUBLIC_POSTHOG_HOST is set", async () => {
    const { PostHogProvider } = await import("@/components/posthog-provider");
    render(
      <PostHogProvider>
        <div>child</div>
      </PostHogProvider>
    );
    act(() => {});
    expect(mockPosthogInit).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        api_host: "https://custom.posthog.example.com",
      })
    );
  });
});
