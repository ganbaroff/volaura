import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();
const mockGetToken = vi.fn();

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  };
});

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

const mockGetMyOrganization = vi.fn();
const mockListOrganizations = vi.fn();
const mockCreateOrganization = vi.fn();
const mockUpdateMyOrganization = vi.fn();

vi.mock("@/lib/api/generated", () => ({
  getMyOrganizationApiOrganizationsMeGet: (...args: unknown[]) => mockGetMyOrganization(...args),
  listOrganizationsApiOrganizationsGet: (...args: unknown[]) => mockListOrganizations(...args),
  createOrganizationApiOrganizationsPost: (...args: unknown[]) => mockCreateOrganization(...args),
  updateMyOrganizationApiOrganizationsMePut: (...args: unknown[]) => mockUpdateMyOrganization(...args),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import {
  useMyOrganization,
  useOrganizations,
  useCreateOrganization,
  useUpdateOrganization,
  useOrgDashboard,
  useCollectiveAura,
  useCreateIntroRequest,
  useProfessionalSearch,
  useSavedSearches,
  useCreateSavedSearch,
  useDeleteSavedSearch,
  useOrgProfessionals,
} from "../queries/use-organizations";
import type {
  CollectiveAuraData,
  IntroRequestPayload,
  IntroRequestResult,
  ProfessionalSearchPayload,
  ProfessionalSearchResultItem,
  SavedSearchItem,
  SaveSearchPayload,
} from "../queries/use-organizations";

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

const ORG: Record<string, unknown> = {
  id: "org_001",
  name: "Test Org",
  slug: "test-org",
  created_at: "2026-01-01T00:00:00Z",
};

const DASHBOARD_STATS = {
  completion_rate: 0.72,
  avg_aura: 68.4,
  badge_distribution: { platinum: 2, gold: 5, silver: 10, bronze: 8 },
};

const COLLECTIVE_AURA: CollectiveAuraData = {
  org_id: "org_001",
  count: 25,
  avg_aura: 71.3,
  trend: 2.1,
};

const INTRO_RESULT: IntroRequestResult = {
  id: "intro_001",
  org_id: "org_001",
  professional_id: "prof_001",
  project_name: "AI Platform",
  timeline: "normal",
  message: "Looking forward to connecting",
  status: "pending",
  created_at: "2026-04-01T00:00:00Z",
};

const SEARCH_RESULT: ProfessionalSearchResultItem = {
  professional_id: "prof_001",
  username: "john_doe",
  display_name: "John Doe",
  overall_score: 82.5,
  badge_tier: "gold",
  elite_status: false,
  location: "Baku",
  languages: ["az", "en"],
  similarity: 0.91,
};

const SAVED_SEARCH: SavedSearchItem = {
  id: "ss_001",
  org_id: "org_001",
  name: "Senior Engineers Baku",
  filters: { query: "senior engineer", min_aura: 70 },
  notify_on_match: true,
  last_checked_at: "2026-04-18T00:00:00Z",
  created_at: "2026-04-01T00:00:00Z",
};

const ORG_PROFESSIONAL = {
  professional_id: "prof_001",
  username: "jane_doe",
  status: "active",
  assigned_at: "2026-03-01T00:00:00Z",
};

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyOrganization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns org data on success", async () => {
    mockGetMyOrganization.mockResolvedValue({ data: ORG, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyOrganization(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(ORG);
  });

  it("throws when SDK returns error", async () => {
    mockGetMyOrganization.mockResolvedValue({ data: null, error: { message: "Not found" } });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyOrganization(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Not found");
  });

  it("uses ['organizations', 'me'] as query key", async () => {
    mockGetMyOrganization.mockResolvedValue({ data: ORG, error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyOrganization(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["organizations", "me"])).toEqual(ORG);
  });

  it("query is not stale immediately after fetch", async () => {
    mockGetMyOrganization.mockResolvedValue({ data: ORG, error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyOrganization(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["organizations", "me"])?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useOrganizations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns org list on success", async () => {
    mockListOrganizations.mockResolvedValue({ data: [ORG], error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrganizations(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([ORG]);
  });

  it("returns empty array when data is null", async () => {
    mockListOrganizations.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrganizations(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });

  it("throws when SDK returns error", async () => {
    mockListOrganizations.mockResolvedValue({
      data: null,
      error: { code: "ORG_LIST_FAILED", message: "Server error" },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrganizations(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Server error");
  });

  it("uses params in query key", async () => {
    mockListOrganizations.mockResolvedValue({ data: [ORG], error: null });
    const params = { limit: 10, offset: 0 };
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useOrganizations(params), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["organizations", "list", params])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateOrganization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns created org on success", async () => {
    mockCreateOrganization.mockResolvedValue({ data: ORG, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateOrganization(), { wrapper });

    await act(async () => {
      result.current.mutate({ name: "Test Org", slug: "test-org" } as never);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(ORG);
  });

  it("invalidates ['organizations'] on success", async () => {
    mockCreateOrganization.mockResolvedValue({ data: ORG, error: null });
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateOrganization(), { wrapper });

    await act(async () => {
      result.current.mutate({ name: "Test Org", slug: "test-org" } as never);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["organizations"] });
  });

  it("surfaces error when SDK returns error", async () => {
    mockCreateOrganization.mockResolvedValue({
      data: null,
      error: { code: "SLUG_TAKEN", message: "Conflict" },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateOrganization(), { wrapper });

    await act(async () => {
      result.current.mutate({ name: "Dup Org" } as never);
    });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Conflict");
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useUpdateOrganization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns updated org on success", async () => {
    const updated = { ...ORG, name: "Updated Org" };
    mockUpdateMyOrganization.mockResolvedValue({ data: updated, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUpdateOrganization(), { wrapper });

    await act(async () => {
      result.current.mutate({ name: "Updated Org" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(updated);
  });

  it("invalidates ['organizations', 'me'] on success", async () => {
    mockUpdateMyOrganization.mockResolvedValue({ data: ORG, error: null });
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useUpdateOrganization(), { wrapper });

    await act(async () => {
      result.current.mutate({ name: "New Name" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["organizations", "me"] });
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useOrgDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns dashboard stats on success", async () => {
    mockApiFetch.mockResolvedValue(DASHBOARD_STATS);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrgDashboard(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(DASHBOARD_STATS);
  });

  it("calls correct endpoint with auth token", async () => {
    mockApiFetch.mockResolvedValue(DASHBOARD_STATS);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrgDashboard(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/organizations/me/dashboard", {
      token: "test-token",
    });
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrgDashboard(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("uses ['organizations', 'me', 'dashboard'] as query key", async () => {
    mockApiFetch.mockResolvedValue(DASHBOARD_STATS);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useOrgDashboard(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["organizations", "me", "dashboard"])).toEqual(DASHBOARD_STATS);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCollectiveAura", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when orgId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useCollectiveAura(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("returns collective aura data on success", async () => {
    mockApiFetch.mockResolvedValue(COLLECTIVE_AURA);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCollectiveAura("org_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(COLLECTIVE_AURA);
  });

  it("calls correct endpoint with orgId and token", async () => {
    mockApiFetch.mockResolvedValue(COLLECTIVE_AURA);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCollectiveAura("org_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/organizations/org_001/collective-aura",
      { token: "test-token" }
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCollectiveAura("org_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("uses orgId in query key", async () => {
    mockApiFetch.mockResolvedValue(COLLECTIVE_AURA);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCollectiveAura("org_001"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["organizations", "org_001", "collective-aura"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateIntroRequest", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  const PAYLOAD: IntroRequestPayload = {
    professional_id: "prof_001",
    project_name: "AI Platform",
    timeline: "normal",
    message: "Let's connect",
  };

  it("returns intro request result on success", async () => {
    mockApiFetch.mockResolvedValue(INTRO_RESULT);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateIntroRequest(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(INTRO_RESULT);
  });

  it("calls correct endpoint with auth token", async () => {
    mockApiFetch.mockResolvedValue(INTRO_RESULT);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateIntroRequest(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/organizations/intro-requests",
      expect.objectContaining({ token: "test-token", method: "POST" })
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateIntroRequest(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useProfessionalSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  const PAYLOAD: ProfessionalSearchPayload = {
    query: "senior frontend",
    min_aura: 70,
    badge_tier: "gold",
    limit: 10,
  };

  it("returns search results on success", async () => {
    mockApiFetch.mockResolvedValue([SEARCH_RESULT]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfessionalSearch(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([SEARCH_RESULT]);
  });

  it("calls correct endpoint with token and applies default limit", async () => {
    mockApiFetch.mockResolvedValue([SEARCH_RESULT]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfessionalSearch(), { wrapper });

    await act(async () => {
      result.current.mutate({ query: "engineer" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/organizations/search/professionals",
      expect.objectContaining({
        token: "test-token",
        method: "POST",
        body: expect.stringContaining('"limit":20'),
      })
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useProfessionalSearch(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useSavedSearches", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns saved searches on success", async () => {
    mockApiFetch.mockResolvedValue([SAVED_SEARCH]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSavedSearches(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([SAVED_SEARCH]);
  });

  it("calls correct endpoint with auth token", async () => {
    mockApiFetch.mockResolvedValue([SAVED_SEARCH]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSavedSearches(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/organizations/saved-searches", {
      token: "test-token",
    });
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSavedSearches(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("uses ['organizations', 'saved-searches'] as query key", async () => {
    mockApiFetch.mockResolvedValue([SAVED_SEARCH]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useSavedSearches(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["organizations", "saved-searches"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateSavedSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  const PAYLOAD: SaveSearchPayload = {
    name: "Senior Engineers Baku",
    filters: { query: "senior engineer", min_aura: 70 },
    notify_on_match: true,
  };

  it("returns created saved search on success", async () => {
    mockApiFetch.mockResolvedValue(SAVED_SEARCH);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateSavedSearch(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(SAVED_SEARCH);
  });

  it("invalidates ['organizations', 'saved-searches'] on success", async () => {
    mockApiFetch.mockResolvedValue(SAVED_SEARCH);
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateSavedSearch(), { wrapper });

    await act(async () => {
      result.current.mutate(PAYLOAD);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["organizations", "saved-searches"],
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDeleteSavedSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls correct DELETE endpoint with searchId", async () => {
    mockApiFetch.mockResolvedValue(undefined);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDeleteSavedSearch(), { wrapper });

    await act(async () => {
      result.current.mutate("ss_001");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/organizations/saved-searches/ss_001",
      expect.objectContaining({ token: "test-token", method: "DELETE" })
    );
  });

  it("invalidates ['organizations', 'saved-searches'] on success", async () => {
    mockApiFetch.mockResolvedValue(undefined);
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useDeleteSavedSearch(), { wrapper });

    await act(async () => {
      result.current.mutate("ss_001");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["organizations", "saved-searches"],
    });
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDeleteSavedSearch(), { wrapper });

    await act(async () => {
      result.current.mutate("ss_001");
    });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useOrgProfessionals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns professionals list on success", async () => {
    mockApiFetch.mockResolvedValue([ORG_PROFESSIONAL]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrgProfessionals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([ORG_PROFESSIONAL]);
  });

  it("calls base endpoint with no params", async () => {
    mockApiFetch.mockResolvedValue([ORG_PROFESSIONAL]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrgProfessionals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/organizations/me/professionals",
      { token: "test-token" }
    );
  });

  it("appends query params when provided", async () => {
    mockApiFetch.mockResolvedValue([ORG_PROFESSIONAL]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useOrgProfessionals({ status: "active", limit: 10, offset: 20 }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledUrl = mockApiFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("status=active");
    expect(calledUrl).toContain("limit=10");
    expect(calledUrl).toContain("offset=20");
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOrgProfessionals(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("uses params in query key", async () => {
    mockApiFetch.mockResolvedValue([ORG_PROFESSIONAL]);
    const params = { status: "active", limit: 5 };
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useOrgProfessionals(params), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(
      qc.getQueryData(["organizations", "me", "professionals", params])
    ).toBeDefined();
  });
});
