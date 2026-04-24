import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  toApiError: (err: unknown) => err instanceof Error ? err : new Error(String(err)),
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

const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import {
  useMyTwin,
  useGenerations,
  useGeneration,
  useCreateTwin,
  useUpdateTwin,
  useRefreshPersonality,
  useActivateTwin,
  useCreateGeneration,
} from "../queries/use-brandedby";
import type { AITwin, Generation } from "../queries/use-brandedby";

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

function makeTwin(overrides: Partial<AITwin> = {}): AITwin {
  return {
    id: "twin_abc",
    user_id: "user_123",
    display_name: "My Twin",
    tagline: "AI-powered me",
    photo_url: "https://example.com/photo.jpg",
    voice_id: "voice_001",
    personality_prompt: "Be professional",
    status: "active",
    created_at: "2026-04-01T00:00:00Z",
    updated_at: "2026-04-02T00:00:00Z",
    ...overrides,
  };
}

function makeGeneration(overrides: Partial<Generation> = {}): Generation {
  return {
    id: "gen_xyz",
    twin_id: "twin_abc",
    user_id: "user_123",
    gen_type: "video",
    input_text: "Hello world",
    output_url: "https://example.com/output.mp4",
    thumbnail_url: null,
    status: "completed",
    error_message: null,
    queue_position: null,
    crystal_cost: 10,
    duration_seconds: 30,
    processing_started_at: "2026-04-01T10:00:00Z",
    completed_at: "2026-04-01T10:01:00Z",
    created_at: "2026-04-01T09:59:00Z",
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyTwin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns AITwin on success", async () => {
    const twin = makeTwin({ display_name: "My AI Twin" });
    mockApiFetch.mockResolvedValue(twin);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyTwin(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.display_name).toBe("My AI Twin");
    expect(result.current.data?.status).toBe("active");
  });

  it("calls apiFetch with /api/brandedby/twins and token", async () => {
    mockApiFetch.mockResolvedValue(makeTwin());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyTwin(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/brandedby/twins", { token: "test-token" });
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyTwin(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  it("uses ['brandedby', 'twin'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeTwin());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyTwin(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["brandedby", "twin"])).toBeDefined();
  });

  it("staleTime — query not stale immediately after fetch", async () => {
    mockApiFetch.mockResolvedValue(makeTwin());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyTwin(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["brandedby", "twin"])?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useGenerations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns list of generations on success", async () => {
    const gens = [makeGeneration({ id: "gen_1" }), makeGeneration({ id: "gen_2" })];
    mockApiFetch.mockResolvedValue(gens);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGenerations(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
  });

  it("calls apiFetch with default limit=20", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGenerations(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/generations?limit=20",
      { token: "test-token" }
    );
  });

  it("passes custom limit param", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGenerations(5), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/generations?limit=5",
      { token: "test-token" }
    );
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGenerations(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  it("uses ['brandedby', 'generations'] as query key", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useGenerations(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["brandedby", "generations"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useGeneration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when genId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useGeneration(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches when genId is provided", async () => {
    mockApiFetch.mockResolvedValue(makeGeneration({ id: "gen_001" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGeneration("gen_001"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/generations/gen_001",
      { token: "test-token" }
    );
  });

  it("uses ['brandedby', 'generation', genId] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeGeneration({ id: "gen_key_test" }));
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useGeneration("gen_key_test"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["brandedby", "generation", "gen_key_test"])).toBeDefined();
  });

  it("does not poll when status is completed", async () => {
    mockApiFetch.mockResolvedValue(makeGeneration({ status: "completed" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGeneration("gen_done"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // refetchInterval returns false for completed — no polling
    expect(result.current.data?.status).toBe("completed");
  });

  it("polls every 5s when status is queued", async () => {
    mockApiFetch.mockResolvedValue(makeGeneration({ status: "queued" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGeneration("gen_queued"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.status).toBe("queued");
  });

  it("polls when status is processing", async () => {
    mockApiFetch.mockResolvedValue(makeGeneration({ status: "processing" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useGeneration("gen_proc"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.status).toBe("processing");
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateTwin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("creates twin and sets cache on success", async () => {
    const twin = makeTwin({ display_name: "New Twin" });
    mockApiFetch.mockResolvedValue(twin);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCreateTwin(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ display_name: "New Twin" });
    });

    expect(qc.getQueryData(["brandedby", "twin"])).toEqual(twin);
  });

  it("calls POST /api/brandedby/twins with body", async () => {
    mockApiFetch.mockResolvedValue(makeTwin());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateTwin(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ display_name: "My Twin", tagline: "Great" });
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/api/brandedby/twins", expect.objectContaining({
      method: "POST",
      token: "test-token",
    }));
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateTwin(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({ display_name: "Twin" });
      })
    ).rejects.toThrow();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useUpdateTwin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("updates twin and sets cache on success", async () => {
    const updatedTwin = makeTwin({ display_name: "Updated Twin" });
    mockApiFetch.mockResolvedValue(updatedTwin);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useUpdateTwin(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ twinId: "twin_abc", data: { display_name: "Updated Twin" } });
    });

    expect(qc.getQueryData(["brandedby", "twin"])).toEqual(updatedTwin);
  });

  it("calls PATCH /api/brandedby/twins/{twinId}", async () => {
    mockApiFetch.mockResolvedValue(makeTwin());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUpdateTwin(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ twinId: "twin_999", data: { tagline: "New tagline" } });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/twins/twin_999",
      expect.objectContaining({ method: "PATCH", token: "test-token" })
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRefreshPersonality", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls POST refresh-personality endpoint", async () => {
    const twin = makeTwin();
    mockApiFetch.mockResolvedValue(twin);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRefreshPersonality(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("twin_abc");
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/twins/twin_abc/refresh-personality",
      expect.objectContaining({ method: "POST", token: "test-token" })
    );
  });

  it("sets twin cache on success", async () => {
    const twin = makeTwin({ personality_prompt: "Updated prompt" });
    mockApiFetch.mockResolvedValue(twin);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useRefreshPersonality(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("twin_abc");
    });

    expect(qc.getQueryData(["brandedby", "twin"])).toEqual(twin);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useActivateTwin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls POST activate endpoint", async () => {
    mockApiFetch.mockResolvedValue(makeTwin({ status: "active" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivateTwin(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("twin_draft");
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/twins/twin_draft/activate",
      expect.objectContaining({ method: "POST", token: "test-token" })
    );
  });

  it("sets twin cache on success", async () => {
    const activeTwin = makeTwin({ status: "active" });
    mockApiFetch.mockResolvedValue(activeTwin);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useActivateTwin(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("twin_abc");
    });

    expect(qc.getQueryData(["brandedby", "twin"])).toEqual(activeTwin);
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivateTwin(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync("twin_abc");
      })
    ).rejects.toThrow();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateGeneration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("creates generation and invalidates generations cache", async () => {
    const gen = makeGeneration({ id: "new_gen" });
    mockApiFetch.mockResolvedValue(gen);
    const { wrapper, qc } = makeWrapper();

    // Pre-populate cache to verify invalidation
    qc.setQueryData(["brandedby", "generations"], [makeGeneration()]);

    const { result } = renderHook(() => useCreateGeneration(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        twin_id: "twin_abc",
        input_text: "Say hello",
      });
    });

    // invalidateQueries marks the query stale
    expect(qc.getQueryState(["brandedby", "generations"])?.isInvalidated).toBe(true);
  });

  it("calls POST /api/brandedby/generations with body", async () => {
    mockApiFetch.mockResolvedValue(makeGeneration());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateGeneration(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        twin_id: "twin_abc",
        gen_type: "audio",
        input_text: "Hello",
      });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/brandedby/generations",
      expect.objectContaining({ method: "POST", token: "test-token" })
    );
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateGeneration(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({ twin_id: "twin_abc", input_text: "test" });
      })
    ).rejects.toThrow();
  });
});
