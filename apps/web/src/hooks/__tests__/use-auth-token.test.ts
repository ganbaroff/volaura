import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";

// ── Supabase mock ─────────────────────────────────────────────────────────────
const mockGetSession = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────
import { useAuthToken } from "../queries/use-auth-token";

// ─────────────────────────────────────────────────────────────────────────────

describe("useAuthToken", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns access_token when session exists", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok_abc123" } },
    });

    const { result } = renderHook(() => useAuthToken());
    const token = await result.current();

    expect(token).toBe("tok_abc123");
  });

  it("returns null when session is null", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: null },
    });

    const { result } = renderHook(() => useAuthToken());
    const token = await result.current();

    expect(token).toBeNull();
  });

  it("returns null when session has no access_token", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: {} },
    });

    const { result } = renderHook(() => useAuthToken());
    const token = await result.current();

    expect(token).toBeNull();
  });

  it("calls createClient on each invocation", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok_xyz" } },
    });

    const { result } = renderHook(() => useAuthToken());
    await result.current();
    await result.current();

    // getSession called twice — once per call
    expect(mockGetSession).toHaveBeenCalledTimes(2);
  });

  it("returns a stable callback reference across re-renders", () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    const { result, rerender } = renderHook(() => useAuthToken());
    const first = result.current;
    rerender();
    const second = result.current;

    expect(first).toBe(second);
  });

  it("propagates getSession errors (does not swallow them)", async () => {
    mockGetSession.mockRejectedValue(new Error("network error"));

    const { result } = renderHook(() => useAuthToken());

    await expect(result.current()).rejects.toThrow("network error");
  });

  it("returns empty string when access_token is an empty string", async () => {
    // The hook uses `?? null` (nullish coalescing), so empty string is NOT null —
    // it is a valid (though unusual) token value returned as-is.
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "" } },
    });

    const { result } = renderHook(() => useAuthToken());
    const token = await result.current();

    expect(token).toBe("");
  });
});
