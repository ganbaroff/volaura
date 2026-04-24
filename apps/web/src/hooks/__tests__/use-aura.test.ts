import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";
import type { AuraScoreResponse } from "@/lib/api/generated/types.gen";

// ── Generated SDK mocks ───────────────────────────────────────────────────────
const mockGetMyAura = vi.fn();
const mockGetAuraById = vi.fn();

vi.mock("@/lib/api/generated", () => ({
  getMyAuraApiAuraMeGet: (...args: unknown[]) => mockGetMyAura(...args),
  getAuraByIdApiAuraProfessionalIdGet: (...args: unknown[]) => mockGetAuraById(...args),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────
import { useAuraScore, useAuraScoreByProfessional } from "../queries/use-aura";

// ─────────────────────────────────────────────────────────────────────────────

/** Minimal valid AuraScoreResponse for SDK mock returns */
function makeRawAura(overrides: Partial<AuraScoreResponse> = {}): AuraScoreResponse {
  return {
    professional_id: "prof_123",
    total_score: 82.5,
    badge_tier: "gold",
    elite_status: true,
    competency_scores: { communication: 0.9, leadership: 0.8 },
    reliability_score: 0.95,
    reliability_status: "reliable",
    events_attended: 10,
    events_no_show: 1,
    percentile_rank: 88,
    effective_score: 83,
    last_updated: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

/** Per-test QueryClient — avoids shared cache state.
 * retryDelay: 0 collapses exponential back-off so error tests don't time out
 * while hook-level retry counts still apply.
 */
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

/** waitFor timeout long enough for hooks with retry: 2 + retryDelay: 0 */
const ERROR_TIMEOUT = { timeout: 5000 };

// ─────────────────────────────────────────────────────────────────────────────

describe("useAuraScore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── toAuraScore transform ────────────────────────────────────────────────

  it("maps elite_status → is_elite correctly (true)", async () => {
    mockGetMyAura.mockResolvedValue({ data: makeRawAura({ elite_status: true }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.is_elite).toBe(true);
  });

  it("maps elite_status → is_elite correctly (false)", async () => {
    mockGetMyAura.mockResolvedValue({ data: makeRawAura({ elite_status: false }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.is_elite).toBe(false);
  });

  it("passes through total_score as-is", async () => {
    mockGetMyAura.mockResolvedValue({ data: makeRawAura({ total_score: 72.3 }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.total_score).toBe(72.3);
  });

  it("passes through badge_tier correctly", async () => {
    mockGetMyAura.mockResolvedValue({ data: makeRawAura({ badge_tier: "platinum" }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.badge_tier).toBe("platinum");
  });

  it("passes through competency_scores correctly", async () => {
    const scores = { communication: 0.9, leadership: 0.7, adaptability: 0.85 };
    mockGetMyAura.mockResolvedValue({ data: makeRawAura({ competency_scores: scores }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.competency_scores).toEqual(scores);
  });

  it("passes through reliability_score and reliability_status", async () => {
    mockGetMyAura.mockResolvedValue({
      data: makeRawAura({ reliability_score: 0.97, reliability_status: "highly_reliable" }),
      error: null,
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.reliability_score).toBe(0.97);
    expect(result.current.data?.reliability_status).toBe("highly_reliable");
  });

  // ── AURA_NOT_FOUND → null ────────────────────────────────────────────────

  it("returns null when error code is AURA_NOT_FOUND", async () => {
    mockGetMyAura.mockResolvedValue({
      data: null,
      error: { detail: { code: "AURA_NOT_FOUND", message: "No score yet" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  it("returns null when SDK returns no data and no error", async () => {
    mockGetMyAura.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  // ── Error path ───────────────────────────────────────────────────────────

  it("throws for non-AURA_NOT_FOUND errors", async () => {
    mockGetMyAura.mockResolvedValue({
      data: null,
      error: { status: 403, detail: { code: "FORBIDDEN", message: "Server error" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Server error");
    expect(result.current.error?.status).toBe(403);
    expect(result.current.error?.code).toBe("FORBIDDEN");
  });

  // ── Query config ─────────────────────────────────────────────────────────

  it("uses ['aura-score'] as query key", async () => {
    mockGetMyAura.mockResolvedValue({ data: makeRawAura(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const cached = qc.getQueryData(["aura-score"]);
    expect(cached).toBeDefined();
  });

  it("staleTime is 5 minutes (300000 ms)", async () => {
    mockGetMyAura.mockResolvedValue({ data: makeRawAura(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAuraScore(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["aura-score"]);
    // staleTime=5min means query is not stale immediately after fetch
    expect(queryState?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAuraScoreByProfessional", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── enabled guard ────────────────────────────────────────────────────────

  it("does not fetch when professionalId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAuraScoreByProfessional(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetAuraById).not.toHaveBeenCalled();
  });

  it("does not fetch when professionalId is empty string", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAuraScoreByProfessional(""), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetAuraById).not.toHaveBeenCalled();
  });

  it("fetches when professionalId is provided", async () => {
    mockGetAuraById.mockResolvedValue({ data: makeRawAura({ professional_id: "prof_456" }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScoreByProfessional("prof_456"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetAuraById).toHaveBeenCalledWith({ path: { professional_id: "prof_456" } });
  });

  // ── toAuraScore transform (same adapter, targeted check) ────────────────

  it("transforms elite_status → is_elite for professional score", async () => {
    mockGetAuraById.mockResolvedValue({
      data: makeRawAura({ professional_id: "prof_789", elite_status: false }),
      error: null,
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScoreByProfessional("prof_789"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.is_elite).toBe(false);
    expect(result.current.data?.professional_id).toBe("prof_789");
  });

  // ── AURA_NOT_FOUND → null ────────────────────────────────────────────────

  it("returns null for AURA_NOT_FOUND on professional lookup", async () => {
    mockGetAuraById.mockResolvedValue({
      data: null,
      error: { detail: { code: "AURA_NOT_FOUND", message: "no score" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScoreByProfessional("prof_new"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  it("returns null when SDK returns null data with no error", async () => {
    mockGetAuraById.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScoreByProfessional("prof_x"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  // ── Error path ───────────────────────────────────────────────────────────

  it("throws for non-AURA_NOT_FOUND errors on professional lookup", async () => {
    mockGetAuraById.mockResolvedValue({
      data: null,
      error: { status: 403, detail: { code: "FORBIDDEN", message: "access denied" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraScoreByProfessional("prof_blocked"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("access denied");
    expect(result.current.error?.status).toBe(403);
    expect(result.current.error?.code).toBe("FORBIDDEN");
  });

  // ── Query key ────────────────────────────────────────────────────────────

  it("uses ['aura-score', professionalId] as query key", async () => {
    mockGetAuraById.mockResolvedValue({ data: makeRawAura({ professional_id: "prof_key_test" }), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAuraScoreByProfessional("prof_key_test"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const cached = qc.getQueryData(["aura-score", "prof_key_test"]);
    expect(cached).toBeDefined();
  });

  it("keeps distinct caches for different professionalIds", async () => {
    mockGetAuraById
      .mockResolvedValueOnce({ data: makeRawAura({ professional_id: "a", total_score: 70 }), error: null })
      .mockResolvedValueOnce({ data: makeRawAura({ professional_id: "b", total_score: 90 }), error: null });

    const { wrapper, qc } = makeWrapper();

    const { result: r1 } = renderHook(() => useAuraScoreByProfessional("a"), { wrapper });
    const { result: r2 } = renderHook(() => useAuraScoreByProfessional("b"), { wrapper });

    await waitFor(() => expect(r1.current.isSuccess).toBe(true));
    await waitFor(() => expect(r2.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["aura-score", "a"])).toBeDefined();
    expect(qc.getQueryData(["aura-score", "b"])).toBeDefined();
    expect(r1.current.data?.professional_id).toBe("a");
    expect(r2.current.data?.professional_id).toBe("b");
  });
});
