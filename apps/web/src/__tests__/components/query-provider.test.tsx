import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Hoisted mocks ─────────────────────────────────────────────────────────────

const { mockConfigureApiClient, MockQueryClient, capturedOptions, mockQCPImpl } = vi.hoisted(() => {
  const mockConfigureApiClient = vi.fn();
  const capturedOptions: { value: Record<string, unknown> } = { value: {} };
  const MockQueryClient = vi.fn(function (this: unknown, options: Record<string, unknown>) {
    capturedOptions.value = options;
    return { _options: options };
  });
  const mockQCPImpl = vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="query-client-provider">{children}</div>
  ));
  return { mockConfigureApiClient, MockQueryClient, capturedOptions, mockQCPImpl };
});

vi.mock("@/lib/api/configure-client", () => ({
  configureApiClient: mockConfigureApiClient,
}));

vi.mock("@tanstack/react-query", () => ({
  QueryClient: MockQueryClient,
  QueryClientProvider: (props: { children: React.ReactNode; client: unknown }) =>
    mockQCPImpl(props),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { QueryProvider } from "@/components/query-provider";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("QueryProvider — module-level side effects", () => {
  it("calls configureApiClient at module load before any render", () => {
    expect(mockConfigureApiClient).toHaveBeenCalled();
  });
});

describe("QueryProvider — rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedOptions.value = {};
  });

  it("renders children inside QueryClientProvider", () => {
    render(
      <QueryProvider>
        <div>child content</div>
      </QueryProvider>
    );
    expect(screen.getByTestId("query-client-provider")).toBeInTheDocument();
    expect(screen.getByText("child content")).toBeInTheDocument();
  });

  it("children are rendered and accessible", () => {
    render(
      <QueryProvider>
        <span data-testid="inner">hello</span>
      </QueryProvider>
    );
    expect(screen.getByTestId("inner")).toBeInTheDocument();
    expect(screen.getByText("hello")).toBeInTheDocument();
  });
});

describe("QueryProvider — QueryClient configuration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedOptions.value = {};
  });

  it("creates QueryClient with staleTime of 60000ms", () => {
    render(
      <QueryProvider>
        <div>child</div>
      </QueryProvider>
    );
    const opts = capturedOptions.value as {
      defaultOptions?: { queries?: { staleTime?: number } };
    };
    expect(opts.defaultOptions?.queries?.staleTime).toBe(60 * 1000);
  });

  it("creates QueryClient with refetchOnWindowFocus false", () => {
    render(
      <QueryProvider>
        <div>child</div>
      </QueryProvider>
    );
    const opts = capturedOptions.value as {
      defaultOptions?: { queries?: { refetchOnWindowFocus?: boolean } };
    };
    expect(opts.defaultOptions?.queries?.refetchOnWindowFocus).toBe(false);
  });

  it("QueryClient is stable across re-renders (useState lazy init)", () => {
    const { rerender } = render(
      <QueryProvider>
        <div>child</div>
      </QueryProvider>
    );
    const firstCallCount = MockQueryClient.mock.calls.length;
    rerender(
      <QueryProvider>
        <div>child updated</div>
      </QueryProvider>
    );
    expect(MockQueryClient.mock.calls.length).toBe(firstCallCount);
  });
});
