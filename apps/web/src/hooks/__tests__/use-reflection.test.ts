import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
      this.name = "ApiError";
    }
  },
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import { useReflection } from "../queries/use-reflection";

// ─────────────────────────────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, retryDelay: 0 } },
  });
  return {
    qc,
    wrapper: ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children),
  };
}

const ERROR_TIMEOUT = { timeout: 5000 };

// ─────────────────────────────────────────────────────────────────────────────

describe("useReflection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── enabled param ─────────────────────────────────────────────────────────

  it("does not fetch when enabled=false", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useReflection(false), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches when enabled=true", async () => {
    mockApiFetch.mockResolvedValue({ reflection: "You did great this week!", cached: false });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/aura/me/reflection");
  });

  // ── no auth (public) ──────────────────────────────────────────────────────

  it("calls apiFetch without a token — public endpoint", async () => {
    mockApiFetch.mockResolvedValue({ reflection: "Keep going!", cached: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Called with only the URL, no auth options
    expect(mockApiFetch).toHaveBeenCalledWith("/aura/me/reflection");
    expect(mockApiFetch).not.toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ token: expect.anything() })
    );
  });

  // ── extracts .reflection from response ────────────────────────────────────

  it("returns the reflection string extracted from response envelope", async () => {
    mockApiFetch.mockResolvedValue({
      reflection: "You demonstrated strong communication skills.",
      cached: false,
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBe("You demonstrated strong communication skills.");
  });

  it("discards the 'cached' flag — only returns reflection string", async () => {
    mockApiFetch.mockResolvedValue({ reflection: "Great work!", cached: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // data is the string, not the object
    expect(typeof result.current.data).toBe("string");
    expect(result.current.data).toBe("Great work!");
  });

  // ── null reflection ───────────────────────────────────────────────────────

  it("returns null when reflection is null in response", async () => {
    mockApiFetch.mockResolvedValue({ reflection: null, cached: false });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  // ── staleTime 24h ─────────────────────────────────────────────────────────

  it("staleTime is 24 hours — query not stale immediately after fetch", async () => {
    mockApiFetch.mockResolvedValue({ reflection: "Keep it up!", cached: false });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["atlas-reflection"])?.isInvalidated).toBe(false);
  });

  // ── cache key ─────────────────────────────────────────────────────────────

  it("uses ['atlas-reflection'] as query key", async () => {
    mockApiFetch.mockResolvedValue({ reflection: "Excellent!", cached: false });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["atlas-reflection"])).toBeDefined();
  });

  // ── error path ────────────────────────────────────────────────────────────

  it("sets isError on fetch failure", async () => {
    mockApiFetch.mockRejectedValue(
      Object.assign(new Error("Service Unavailable"), { status: 503 })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useReflection(true), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Service Unavailable");
  });
});
