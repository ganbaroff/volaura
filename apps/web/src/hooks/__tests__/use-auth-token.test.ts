import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";

// ── Mock getFreshAccessToken (the module useAuthToken now delegates to) ───────
const mockGetFreshAccessToken = vi.fn();

vi.mock("@/lib/api/get-fresh-token", () => ({
  getFreshAccessToken: (...args: unknown[]) => mockGetFreshAccessToken(...args),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────
import { useAuthToken } from "../queries/use-auth-token";

// ─────────────────────────────────────────────────────────────────────────────

describe("useAuthToken", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns token from getFreshAccessToken", async () => {
    mockGetFreshAccessToken.mockResolvedValue("tok_abc123");

    const { result } = renderHook(() => useAuthToken());
    const token = await result.current();

    expect(token).toBe("tok_abc123");
  });

  it("returns null when getFreshAccessToken returns null", async () => {
    mockGetFreshAccessToken.mockResolvedValue(null);

    const { result } = renderHook(() => useAuthToken());
    const token = await result.current();

    expect(token).toBeNull();
  });

  it("calls getFreshAccessToken on each invocation", async () => {
    mockGetFreshAccessToken.mockResolvedValue("tok_xyz");

    const { result } = renderHook(() => useAuthToken());
    await result.current();
    await result.current();

    expect(mockGetFreshAccessToken).toHaveBeenCalledTimes(2);
  });

  it("returns a stable callback reference across re-renders", () => {
    mockGetFreshAccessToken.mockResolvedValue(null);

    const { result, rerender } = renderHook(() => useAuthToken());
    const first = result.current;
    rerender();
    const second = result.current;

    expect(first).toBe(second);
  });
});
