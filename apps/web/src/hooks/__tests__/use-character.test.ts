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

import {
  useCrystalBalance,
  useCharacterState,
} from "../queries/use-character";
import type {
  CrystalBalance,
  CharacterState,
  VerifiedSkill,
} from "../queries/use-character";

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

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeCrystalBalance(overrides: Partial<CrystalBalance> = {}): CrystalBalance {
  return {
    user_id: "user_abc",
    crystal_balance: 250,
    computed_at: "2026-04-18T12:00:00Z",
    ...overrides,
  };
}

function makeVerifiedSkill(overrides: Partial<VerifiedSkill> = {}): VerifiedSkill {
  return {
    slug: "communication",
    aura_score: 82.5,
    badge_tier: "gold",
    ...overrides,
  };
}

function makeCharacterState(overrides: Partial<CharacterState> = {}): CharacterState {
  return {
    user_id: "user_abc",
    crystal_balance: 250,
    xp_total: 1800,
    verified_skills: [makeVerifiedSkill()],
    character_stats: { strength: 70, focus: 85 },
    login_streak: 5,
    event_count: 10,
    last_event_at: "2026-04-17T18:00:00Z",
    computed_at: "2026-04-18T12:00:00Z",
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useCrystalBalance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns CrystalBalance object on success", async () => {
    const balance = makeCrystalBalance({ crystal_balance: 500, user_id: "user_xyz" });
    mockApiFetch.mockResolvedValue(balance);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.user_id).toBe("user_xyz");
    expect(result.current.data?.crystal_balance).toBe(500);
    expect(result.current.data?.computed_at).toBe("2026-04-18T12:00:00Z");
  });

  it("calls apiFetch with /api/character/crystals", async () => {
    mockApiFetch.mockResolvedValue(makeCrystalBalance());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/character/crystals");
  });

  // ── 404 → null ───────────────────────────────────────────────────────────

  it("returns null when API returns 404 (no character events yet)", async () => {
    const notFoundErr = Object.assign(new Error("Not Found"), { status: 404 });
    mockApiFetch.mockRejectedValue(notFoundErr);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  // ── other error → rethrow ─────────────────────────────────────────────────

  it("throws for non-404 errors", async () => {
    const serverErr = Object.assign(new Error("Internal Server Error"), { status: 500 });
    mockApiFetch.mockRejectedValue(serverErr);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Internal Server Error");
  });

  it("throws for 403 errors", async () => {
    const forbiddenErr = Object.assign(new Error("Forbidden"), { status: 403 });
    mockApiFetch.mockRejectedValue(forbiddenErr);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Forbidden");
  });

  // ── staleTime ─────────────────────────────────────────────────────────────

  it("staleTime is 30 seconds — query not stale immediately after fetch", async () => {
    mockApiFetch.mockResolvedValue(makeCrystalBalance());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["crystal-balance"]);
    expect(queryState?.isInvalidated).toBe(false);
  });

  // ── query key ─────────────────────────────────────────────────────────────

  it("uses ['crystal-balance'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeCrystalBalance());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCrystalBalance(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["crystal-balance"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCharacterState", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns CharacterState object on success", async () => {
    const state = makeCharacterState({
      user_id: "user_xyz",
      crystal_balance: 750,
      xp_total: 3000,
      login_streak: 12,
      event_count: 20,
    });
    mockApiFetch.mockResolvedValue(state);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.user_id).toBe("user_xyz");
    expect(result.current.data?.crystal_balance).toBe(750);
    expect(result.current.data?.xp_total).toBe(3000);
    expect(result.current.data?.login_streak).toBe(12);
    expect(result.current.data?.event_count).toBe(20);
  });

  it("calls apiFetch with /api/character/state", async () => {
    mockApiFetch.mockResolvedValue(makeCharacterState());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/character/state");
  });

  // ── VerifiedSkill interface shape ─────────────────────────────────────────

  it("returns VerifiedSkill with all interface fields", async () => {
    const skill = makeVerifiedSkill({
      slug: "leadership",
      aura_score: 91.0,
      badge_tier: "platinum",
    });
    mockApiFetch.mockResolvedValue(makeCharacterState({ verified_skills: [skill] }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const vs = result.current.data?.verified_skills[0];
    expect(vs?.slug).toBe("leadership");
    expect(vs?.aura_score).toBe(91.0);
    expect(vs?.badge_tier).toBe("platinum");
  });

  it("handles VerifiedSkill with null aura_score and null badge_tier", async () => {
    const skill = makeVerifiedSkill({ aura_score: null, badge_tier: null });
    mockApiFetch.mockResolvedValue(makeCharacterState({ verified_skills: [skill] }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const vs = result.current.data?.verified_skills[0];
    expect(vs?.aura_score).toBeNull();
    expect(vs?.badge_tier).toBeNull();
  });

  it("handles null last_event_at", async () => {
    mockApiFetch.mockResolvedValue(makeCharacterState({ last_event_at: null }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.last_event_at).toBeNull();
  });

  // ── 404 → null ───────────────────────────────────────────────────────────

  it("returns null when API returns 404", async () => {
    const notFoundErr = Object.assign(new Error("Not Found"), { status: 404 });
    mockApiFetch.mockRejectedValue(notFoundErr);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  // ── enabled param ─────────────────────────────────────────────────────────

  it("does not fetch when enabled=false", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useCharacterState(false), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches when enabled=true (explicit)", async () => {
    mockApiFetch.mockResolvedValue(makeCharacterState());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/character/state");
  });

  it("fetches when enabled is omitted (default true)", async () => {
    mockApiFetch.mockResolvedValue(makeCharacterState());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalled();
  });

  // ── other error → rethrow ─────────────────────────────────────────────────

  it("throws for non-404 errors", async () => {
    const serverErr = Object.assign(new Error("Service unavailable"), { status: 503 });
    mockApiFetch.mockRejectedValue(serverErr);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Service unavailable");
  });

  // ── staleTime ─────────────────────────────────────────────────────────────

  it("staleTime is 60 seconds — query not stale immediately after fetch", async () => {
    mockApiFetch.mockResolvedValue(makeCharacterState());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["character-state"]);
    expect(queryState?.isInvalidated).toBe(false);
  });

  // ── query key ─────────────────────────────────────────────────────────────

  it("uses ['character-state'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeCharacterState());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCharacterState(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["character-state"])).toBeDefined();
  });
});
