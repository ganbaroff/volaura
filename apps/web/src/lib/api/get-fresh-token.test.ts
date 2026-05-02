/**
 * Unit tests for getFreshAccessToken.
 *
 * Covers: fresh token passthrough, refresh on expiry, refresh within 60s buffer,
 * refresh failure fallback, missing session, and getSession() throw.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { getFreshAccessToken } from "./get-fresh-token";
import { useAuthStore } from "@/stores/auth-store";

// ── JWT helpers ───────────────────────────────────────────────────────────────

/** Build a minimal valid JWT with the given exp (unix seconds). */
function makeToken(expSeconds: number): string {
  const payload = btoa(JSON.stringify({ sub: "user-abc", exp: expSeconds }))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  return `eyJhbGciOiJIUzI1NiJ9.${payload}.sig`;
}

const now = () => Math.floor(Date.now() / 1000);

const FRESH_TOKEN    = makeToken(now() + 3600); // valid 1 hour from now
const STALE_TOKEN    = makeToken(now() - 60);   // expired 1 minute ago
const EXPIRING_TOKEN = makeToken(now() + 30);   // expires in 30s (< 60s buffer)
const REFRESHED_TOKEN = makeToken(now() + 3600); // new token after refresh

// ── Mocks ─────────────────────────────────────────────────────────────────────

const { mockGetSession, mockRefreshSession } = vi.hoisted(() => ({
  mockGetSession: vi.fn(),
  mockRefreshSession: vi.fn(),
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
      refreshSession: mockRefreshSession,
    },
  }),
}));

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("getFreshAccessToken", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clear();
  });

  it("returns fresh token directly — no refreshSession call", async () => {
    mockGetSession.mockResolvedValue({ data: { session: { access_token: FRESH_TOKEN } } });

    const token = await getFreshAccessToken();

    expect(token).toBe(FRESH_TOKEN);
    expect(mockRefreshSession).not.toHaveBeenCalled();
  });

  it("calls refreshSession and returns new token when access_token is expired", async () => {
    mockGetSession.mockResolvedValue({ data: { session: { access_token: STALE_TOKEN } } });
    mockRefreshSession.mockResolvedValue({
      data: { session: { access_token: REFRESHED_TOKEN } },
      error: null,
    });

    const token = await getFreshAccessToken();

    expect(mockRefreshSession).toHaveBeenCalledOnce();
    expect(token).toBe(REFRESHED_TOKEN);
  });

  it("calls refreshSession when token expires within the 60s buffer window", async () => {
    mockGetSession.mockResolvedValue({ data: { session: { access_token: EXPIRING_TOKEN } } });
    mockRefreshSession.mockResolvedValue({
      data: { session: { access_token: REFRESHED_TOKEN } },
      error: null,
    });

    const token = await getFreshAccessToken();

    expect(mockRefreshSession).toHaveBeenCalledOnce();
    expect(token).toBe(REFRESHED_TOKEN);
  });

  it("returns the stale token when refreshSession fails — lets API return 401", async () => {
    mockGetSession.mockResolvedValue({ data: { session: { access_token: STALE_TOKEN } } });
    mockRefreshSession.mockResolvedValue({
      data: { session: null },
      error: { message: "Refresh token expired" },
    });

    const token = await getFreshAccessToken();

    // Stale token returned — downstream API call will get 401 and the
    // caller's 401 recovery path (redirect to login) handles it.
    expect(token).toBe(STALE_TOKEN);
  });

  it("returns null when no session exists", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    const token = await getFreshAccessToken();

    expect(token).toBeNull();
    expect(mockRefreshSession).not.toHaveBeenCalled();
  });

  it("returns cached store token when Supabase storage is temporarily empty", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    useAuthStore.getState().setSession({
      access_token: FRESH_TOKEN,
      refresh_token: "refresh-from-store",
      user: { id: "user-1" },
    } as never);

    const token = await getFreshAccessToken();

    expect(token).toBe(FRESH_TOKEN);
    expect(mockRefreshSession).not.toHaveBeenCalled();
  });

  it("refreshes with cached store refresh_token when cached access token is stale", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockRefreshSession.mockResolvedValue({
      data: {
        session: {
          access_token: REFRESHED_TOKEN,
          refresh_token: "refresh-new",
          user: { id: "user-1" },
        },
      },
      error: null,
    });
    useAuthStore.getState().setSession({
      access_token: STALE_TOKEN,
      refresh_token: "refresh-from-store",
      user: { id: "user-1" },
    } as never);

    const token = await getFreshAccessToken();

    expect(mockRefreshSession).toHaveBeenCalledWith({ refresh_token: "refresh-from-store" });
    expect(token).toBe(REFRESHED_TOKEN);
    expect(useAuthStore.getState().session?.access_token).toBe(REFRESHED_TOKEN);
  });

  it("returns null when getSession() throws", async () => {
    mockGetSession.mockRejectedValue(new Error("Storage unavailable"));

    const token = await getFreshAccessToken();

    expect(token).toBeNull();
  });

  it("returns null when refreshSession returns no session and no error", async () => {
    mockGetSession.mockResolvedValue({ data: { session: { access_token: STALE_TOKEN } } });
    mockRefreshSession.mockResolvedValue({ data: { session: null }, error: null });

    const token = await getFreshAccessToken();

    // refresh returned no session — fall back to stale token
    expect(token).toBe(STALE_TOKEN);
  });
});
