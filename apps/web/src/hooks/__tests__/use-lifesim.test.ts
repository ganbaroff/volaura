import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";
import type { FeedResponse, NextChoiceResponse } from "@/lib/api/generated/types.gen";

// ── Generated SDK mocks ───────────────────────────────────────────────────────
const mockGetFeed = vi.fn();
const mockGetNextChoice = vi.fn();
const mockSubmitChoice = vi.fn();
const mockPurchase = vi.fn();

vi.mock("@/lib/api/generated", () => ({
  getFeedApiLifesimFeedGet: (...args: unknown[]) => mockGetFeed(...args),
  getNextChoiceApiLifesimNextChoiceGet: (...args: unknown[]) => mockGetNextChoice(...args),
  submitChoiceApiLifesimChoicePost: (...args: unknown[]) => mockSubmitChoice(...args),
  purchaseShopItemApiLifesimPurchasePost: (...args: unknown[]) => mockPurchase(...args),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────
import {
  useLifesimFeed,
  useLifesimNextChoice,
  useLifesimSubmitChoice,
  useLifesimPurchase,
} from "../queries/use-lifesim";

// ─────────────────────────────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return {
    qc,
    wrapper: ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children),
  };
}

const makeFeedResponse = (overrides: Partial<FeedResponse> = {}): FeedResponse => ({
  data: [],
  ...overrides,
});

const makeNextChoiceResponse = (overrides: Partial<NextChoiceResponse> = {}): NextChoiceResponse => ({
  event: null,
  pool_size: 0,
  ...overrides,
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useLifesimFeed", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns feed data on success", async () => {
    const feed = makeFeedResponse({ data: [{ id: "e1", text: "You started school" } as Record<string, unknown>] });
    mockGetFeed.mockResolvedValue({ data: feed, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimFeed(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.data).toHaveLength(1);
  });

  it("passes limit to SDK query", async () => {
    mockGetFeed.mockResolvedValue({ data: makeFeedResponse(), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimFeed(25), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetFeed).toHaveBeenCalledWith({ query: { limit: 25 } });
  });

  it("defaults limit to 50 when not specified", async () => {
    mockGetFeed.mockResolvedValue({ data: makeFeedResponse(), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimFeed(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetFeed).toHaveBeenCalledWith({ query: { limit: 50 } });
  });

  it("falls back to { data: [] } when SDK returns null data (no error)", async () => {
    mockGetFeed.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimFeed(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({ data: [] });
  });

  it("throws when SDK returns error", async () => {
    mockGetFeed.mockResolvedValue({ data: null, error: { message: "server failure" } });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimFeed(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error?.message).toBe("Failed to fetch life feed");
  });

  it("uses ['lifesim-feed', limit] as query key", async () => {
    mockGetFeed.mockResolvedValue({ data: makeFeedResponse(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useLifesimFeed(50), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["lifesim-feed", 50])).toBeDefined();
  });

  it("keeps distinct caches for different limit values", async () => {
    const feed10 = makeFeedResponse({ data: new Array(10).fill({ id: "x" }) as Record<string, unknown>[] });
    const feed20 = makeFeedResponse({ data: new Array(20).fill({ id: "y" }) as Record<string, unknown>[] });

    mockGetFeed
      .mockResolvedValueOnce({ data: feed10, error: null })
      .mockResolvedValueOnce({ data: feed20, error: null });

    const { wrapper, qc } = makeWrapper();

    const { result: r1 } = renderHook(() => useLifesimFeed(10), { wrapper });
    const { result: r2 } = renderHook(() => useLifesimFeed(20), { wrapper });

    await waitFor(() => expect(r1.current.isSuccess).toBe(true));
    await waitFor(() => expect(r2.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["lifesim-feed", 10])).toBeDefined();
    expect(qc.getQueryData(["lifesim-feed", 20])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useLifesimNextChoice", () => {
  const baseParams = { age: 25, intelligence: 70, social: 60 };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns next choice data on success", async () => {
    const choice = makeNextChoiceResponse({ event: { id: "evt_1", text: "Career offer" }, pool_size: 5 });
    mockGetNextChoice.mockResolvedValue({ data: choice, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimNextChoice(baseParams), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.pool_size).toBe(5);
    expect(result.current.data?.event).not.toBeNull();
  });

  it("passes all params to SDK query", async () => {
    mockGetNextChoice.mockResolvedValue({ data: makeNextChoiceResponse(), error: null });
    const params = { age: 30, intelligence: 80, social: 70, energy: 60, happiness: 90, health: 85, money: 1000, work_experience: 5, category: "career" };
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimNextChoice(params), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetNextChoice).toHaveBeenCalledWith({ query: params });
  });

  it("does not fetch when enabled=false", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useLifesimNextChoice(baseParams, false), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetNextChoice).not.toHaveBeenCalled();
  });

  it("fetches when enabled=true (default)", async () => {
    mockGetNextChoice.mockResolvedValue({ data: makeNextChoiceResponse(), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimNextChoice(baseParams, true), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetNextChoice).toHaveBeenCalledOnce();
  });

  it("falls back to { event: null, pool_size: 0 } when SDK returns null data", async () => {
    mockGetNextChoice.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimNextChoice(baseParams), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({ event: null, pool_size: 0 });
  });

  it("throws when SDK returns error", async () => {
    mockGetNextChoice.mockResolvedValue({ data: null, error: { message: "LLM timeout" } });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimNextChoice(baseParams), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error?.message).toBe("Failed to fetch next choice");
  });

  it("has staleTime: Infinity (does not auto-refetch on window focus)", async () => {
    mockGetNextChoice.mockResolvedValue({ data: makeNextChoiceResponse(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useLifesimNextChoice(baseParams), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Only one fetch on mount — staleTime Infinity means a second fetch should not happen
    expect(mockGetNextChoice).toHaveBeenCalledTimes(1);

    // Query is not stale immediately after success
    const state = qc.getQueryState(["lifesim-next-choice", baseParams]);
    expect(state?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useLifesimSubmitChoice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const submitArgs = {
    event_id: "evt_1",
    choice_index: 0,
    stats_before: { intelligence: 70, social: 60 },
  };

  it("calls SDK with correct body", async () => {
    mockSubmitChoice.mockResolvedValue({ data: { success: true }, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimSubmitChoice(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(submitArgs);
    });

    expect(mockSubmitChoice).toHaveBeenCalledWith({ body: submitArgs });
  });

  it("invalidates ['lifesim-feed'] on success", async () => {
    mockSubmitChoice.mockResolvedValue({ data: { result: "ok" }, error: null });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimSubmitChoice(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(submitArgs);
    });

    const feedInvalidated = invalidateSpy.mock.calls.some(
      (call) => JSON.stringify(call[0]) === JSON.stringify({ queryKey: ["lifesim-feed"] })
    );
    expect(feedInvalidated).toBe(true);
  });

  it("invalidates ['lifesim-next-choice'] on success", async () => {
    mockSubmitChoice.mockResolvedValue({ data: { result: "ok" }, error: null });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimSubmitChoice(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(submitArgs);
    });

    const choiceInvalidated = invalidateSpy.mock.calls.some(
      (call) => JSON.stringify(call[0]) === JSON.stringify({ queryKey: ["lifesim-next-choice"] })
    );
    expect(choiceInvalidated).toBe(true);
  });

  it("throws when SDK returns error", async () => {
    mockSubmitChoice.mockResolvedValue({ data: null, error: { message: "submission rejected" } });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimSubmitChoice(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync(submitArgs)).rejects.toThrow("Choice submission failed");
    });
  });

  it("throws when SDK returns null data with no error", async () => {
    mockSubmitChoice.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimSubmitChoice(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync(submitArgs)).rejects.toThrow(
        "Empty response from choice endpoint"
      );
    });
  });

  it("does not invalidate queries on failure", async () => {
    mockSubmitChoice.mockResolvedValue({ data: null, error: { message: "fail" } });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimSubmitChoice(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(submitArgs).catch(() => undefined);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useLifesimPurchase", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const purchaseArgs = { shop_item: "crystal_pack_10", current_crystals: 50 };

  it("calls SDK with correct body", async () => {
    mockPurchase.mockResolvedValue({ data: { crystals_remaining: 40 }, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(purchaseArgs);
    });

    expect(mockPurchase).toHaveBeenCalledWith({ body: purchaseArgs });
  });

  it("invalidates ['lifesim-feed'] on success", async () => {
    mockPurchase.mockResolvedValue({ data: { crystals_remaining: 45 }, error: null });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(purchaseArgs);
    });

    const feedInvalidated = invalidateSpy.mock.calls.some(
      (call) => JSON.stringify(call[0]) === JSON.stringify({ queryKey: ["lifesim-feed"] })
    );
    expect(feedInvalidated).toBe(true);
  });

  it("invalidates ['aura-score'] on success (crystal balance lives there)", async () => {
    mockPurchase.mockResolvedValue({ data: { crystals_remaining: 45 }, error: null });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(purchaseArgs);
    });

    const auraInvalidated = invalidateSpy.mock.calls.some(
      (call) => JSON.stringify(call[0]) === JSON.stringify({ queryKey: ["aura-score"] })
    );
    expect(auraInvalidated).toBe(true);
  });

  it("invalidates both lifesim-feed and aura-score on success", async () => {
    mockPurchase.mockResolvedValue({ data: { crystals_remaining: 45 }, error: null });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(purchaseArgs);
    });

    expect(invalidateSpy).toHaveBeenCalledTimes(2);
  });

  it("throws when SDK returns error", async () => {
    mockPurchase.mockResolvedValue({ data: null, error: { message: "insufficient crystals" } });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync(purchaseArgs)).rejects.toThrow("Crystal purchase failed");
    });
  });

  it("throws when SDK returns null data with no error", async () => {
    mockPurchase.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync(purchaseArgs)).rejects.toThrow(
        "Empty response from purchase endpoint"
      );
    });
  });

  it("does not invalidate queries on failure", async () => {
    mockPurchase.mockResolvedValue({ data: null, error: { message: "fail" } });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLifesimPurchase(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(purchaseArgs).catch(() => undefined);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
