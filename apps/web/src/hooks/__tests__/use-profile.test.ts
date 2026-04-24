import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";
import type { ProfileResponse } from "@/lib/api/generated/types.gen";

// ── Generated SDK mocks ───────────────────────────────────────────────────────
const mockGetMyProfile = vi.fn();
const mockGetPublicProfile = vi.fn();
const mockUpdateMyProfile = vi.fn();

vi.mock("@/lib/api/generated", () => ({
  getMyProfileApiProfilesMeGet: (...args: unknown[]) => mockGetMyProfile(...args),
  getPublicProfileApiProfilesUsernameGet: (...args: unknown[]) => mockGetPublicProfile(...args),
  updateMyProfileApiProfilesMePut: (...args: unknown[]) => mockUpdateMyProfile(...args),
}));

// ── apiFetch mock ─────────────────────────────────────────────────────────────
const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    detail: string;
    constructor(status: number, code: string, detail: string) {
      super(detail);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
      this.detail = detail;
    }
  },
}));

// ── useAuthToken mock ─────────────────────────────────────────────────────────
const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────
import {
  useProfile,
  usePublicProfile,
  useDiscoverableProfessionals,
  useUpdateProfile,
  useMyVerifications,
  useProfileViews,
} from "../queries/use-profile";

// ─────────────────────────────────────────────────────────────────────────────

function makeRawProfile(overrides: Partial<ProfileResponse> = {}): ProfileResponse {
  return {
    id: "user_abc",
    username: "testuser",
    display_name: "Test User",
    bio: "Hello",
    location: "Baku",
    languages: ["az", "en"],
    is_public: true,
    avatar_url: "https://example.com/avatar.jpg",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    registration_number: 42,
    registration_tier: "early",
    ...overrides,
  };
}

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

describe("useProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("transforms ProfileResponse via toProfile (nullable defaults)", async () => {
    mockGetMyProfile.mockResolvedValue({
      data: makeRawProfile({ display_name: null, bio: null, location: null }),
      error: null,
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfile(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.display_name).toBeNull();
    expect(result.current.data?.bio).toBeNull();
    expect(result.current.data?.location).toBeNull();
  });

  it("applies empty array default when languages is undefined", async () => {
    const raw = makeRawProfile();
    // Simulate undefined languages from API (omitted field)
    (raw as Partial<ProfileResponse>).languages = undefined;
    mockGetMyProfile.mockResolvedValue({ data: raw, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfile(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.languages).toEqual([]);
  });

  it("applies false default when is_public is undefined", async () => {
    const raw = makeRawProfile();
    (raw as Partial<ProfileResponse>).is_public = undefined;
    mockGetMyProfile.mockResolvedValue({ data: raw, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfile(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.is_public).toBe(false);
  });

  it("applies null default when registration_number is undefined", async () => {
    const raw = makeRawProfile();
    (raw as Partial<ProfileResponse>).registration_number = undefined;
    mockGetMyProfile.mockResolvedValue({ data: raw, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfile(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.registration_number).toBeNull();
  });

  it("throws when SDK returns error", async () => {
    mockGetMyProfile.mockResolvedValue({
      data: null,
      error: { status: 401, detail: { code: "UNAUTHORIZED", message: "Session expired" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfile(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Session expired");
    expect(result.current.error?.status).toBe(401);
    expect(result.current.error?.code).toBe("UNAUTHORIZED");
  });

  it("uses ['profile', 'me'] as query key", async () => {
    mockGetMyProfile.mockResolvedValue({ data: makeRawProfile(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useProfile(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["profile", "me"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("usePublicProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not fetch when username is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => usePublicProfile(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetPublicProfile).not.toHaveBeenCalled();
  });

  it("does not fetch when username is empty string", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => usePublicProfile(""), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
  });

  it("fetches with username in path when provided", async () => {
    mockGetPublicProfile.mockResolvedValue({ data: makeRawProfile({ username: "janedoe" }), error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePublicProfile("janedoe"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetPublicProfile).toHaveBeenCalledWith({ path: { username: "janedoe" } });
    expect(result.current.data?.username).toBe("janedoe");
  });

  it("uses ['profile', username] as query key", async () => {
    mockGetPublicProfile.mockResolvedValue({ data: makeRawProfile({ username: "alice" }), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => usePublicProfile("alice"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["profile", "alice"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDiscoverableProfessionals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("tok_org");
  });

  it("fetches without query string when no params provided", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDiscoverableProfessionals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/profiles/public", { token: "tok_org" });
  });

  it("appends limit query param when provided", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDiscoverableProfessionals({ limit: 20 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toContain("limit=20");
  });

  it("appends offset query param when provided", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDiscoverableProfessionals({ offset: 40 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toContain("offset=40");
  });

  it("appends both limit and offset when both provided", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDiscoverableProfessionals({ limit: 10, offset: 30 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toContain("limit=10");
    expect(calledPath).toContain("offset=30");
  });

  it("does not append query string when limit and offset are both undefined", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDiscoverableProfessionals({}), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toBe("/api/profiles/public");
  });

  it("throws ApiError(401) when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDiscoverableProfessionals(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useUpdateProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("invalidates ['profile', 'me'] on success", async () => {
    mockUpdateMyProfile.mockResolvedValue({ data: makeRawProfile(), error: null });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useUpdateProfile(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ display_name: "New Name" });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["profile", "me"] });
  });

  it("returns transformed profile on success", async () => {
    mockUpdateMyProfile.mockResolvedValue({
      data: makeRawProfile({ display_name: "Updated", username: "updateduser" }),
      error: null,
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUpdateProfile(), { wrapper });

    let mutationResult: ReturnType<typeof useUpdateProfile>["data"];
    await act(async () => {
      mutationResult = await result.current.mutateAsync({ display_name: "Updated" });
    });

    expect(mutationResult?.display_name).toBe("Updated");
    expect(mutationResult?.username).toBe("updateduser");
  });

  it("throws when SDK returns error", async () => {
    mockUpdateMyProfile.mockResolvedValue({
      data: null,
      error: { status: 422, detail: { code: "VALIDATION_ERROR", message: "validation failed" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUpdateProfile(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync({ display_name: "" })).rejects.toThrow(
        "validation failed"
      );
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyVerifications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns empty array when token is null (no throw)", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyVerifications(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });

  it("calls apiFetch with correct path when authenticated", async () => {
    mockGetToken.mockResolvedValue("tok_user");
    mockApiFetch.mockResolvedValue([
      {
        id: "v1",
        verifier_name: "Jane Expert",
        verifier_org: "Acme",
        competency_id: "comp_1",
        rating: 5,
        comment: "Excellent",
        verified_at: "2026-01-01T00:00:00Z",
      },
    ]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyVerifications(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/profiles/me/verifications", { token: "tok_user" });
    expect(result.current.data).toHaveLength(1);
  });

  it("uses ['profile', 'verifications'] as query key", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyVerifications(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["profile", "verifications"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useProfileViews", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns zero-state when token is null (no throw)", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfileViews(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({
      total_views: 0,
      week_views: 0,
      recent_viewers: [],
    });
  });

  it("calls apiFetch with correct path when authenticated", async () => {
    mockGetToken.mockResolvedValue("tok_user");
    mockApiFetch.mockResolvedValue({
      total_views: 50,
      week_views: 10,
      recent_viewers: [{ name: "Org A", at: "2026-01-15T10:00:00Z" }],
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfileViews(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/profiles/me/views", { token: "tok_user" });
    expect(result.current.data?.total_views).toBe(50);
    expect(result.current.data?.week_views).toBe(10);
    expect(result.current.data?.recent_viewers).toHaveLength(1);
  });

  it("uses ['profile', 'views'] as query key", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useProfileViews(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["profile", "views"])).toBeDefined();
  });
});
