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

// ── Imports (after mocks) ─────────────────────────────────────────────────────

import {
  useAdminPing,
  useAdminStats,
  useAdminUsers,
  usePendingOrganizations,
  useApproveOrganization,
  useRejectOrganization,
  useSwarmAgents,
  useSwarmProposals,
  useDecideProposal,
  useAdminOverview,
  useAdminLiveEvents,
  useSwarmFindings,
} from "../queries/use-admin";
import type {
  AdminStats,
  AdminUserRow,
  AdminOrgRow,
  AdminOverviewResponse,
  AdminActivityEvent,
  SwarmAgent,
  SwarmProposal,
  SwarmFinding,
} from "../queries/use-admin";

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

function makeAdminStats(overrides: Partial<AdminStats> = {}): AdminStats {
  return {
    total_users: 100,
    total_organizations: 10,
    pending_org_approvals: 2,
    assessments_today: 15,
    avg_aura_score: 72.5,
    pending_grievances: 1,
    ...overrides,
  };
}

function makeAdminUserRow(overrides: Partial<AdminUserRow> = {}): AdminUserRow {
  return {
    id: "user-001",
    username: "johndoe",
    display_name: "John Doe",
    account_type: "professional",
    subscription_status: "free",
    is_platform_admin: false,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeAdminOrgRow(overrides: Partial<AdminOrgRow> = {}): AdminOrgRow {
  return {
    id: "org-001",
    name: "Acme Corp",
    description: "A test org",
    website: "https://acme.test",
    owner_id: "user-001",
    owner_username: "johndoe",
    trust_score: 85,
    verified_at: null,
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeAdminOverview(overrides: Partial<AdminOverviewResponse> = {}): AdminOverviewResponse {
  return {
    activation_rate_24h: 0.42,
    w4_retention: null,
    dau_wau_ratio: 0.3,
    errors_24h: 5,
    runway_months: null,
    presence: {
      volaura_only: 80,
      mindshift_only: 20,
      both_products: 10,
      total_users: 110,
    },
    funnels: [],
    computed_at: "2026-04-18T00:00:00Z",
    stale_after_seconds: 30,
    ...overrides,
  };
}

function makeActivityEvent(overrides: Partial<AdminActivityEvent> = {}): AdminActivityEvent {
  return {
    id: "evt-001",
    product: "volaura",
    event_type: "assessment_completed",
    user_id_prefix: "usr_abc",
    created_at: "2026-04-18T10:00:00Z",
    payload_summary: "competency: communication",
    ...overrides,
  };
}

function makeSwarmAgent(overrides: Partial<SwarmAgent> = {}): SwarmAgent {
  return {
    name: "code-agent",
    display_name: "Code Agent",
    status: "idle",
    last_task: "audit",
    last_run: "2026-04-18T09:00:00Z",
    next_scheduled: null,
    blockers: [],
    tasks_completed: 12,
    tasks_failed: 1,
    ...overrides,
  };
}

function makeSwarmProposal(overrides: Partial<SwarmProposal> = {}): SwarmProposal {
  return {
    id: "prop-001",
    timestamp: "2026-04-18T08:00:00Z",
    agent: "code-agent",
    severity: "medium",
    type: "refactor",
    status: "pending",
    title: "Refactor auth middleware",
    ...overrides,
  };
}

function makeSwarmFinding(overrides: Partial<SwarmFinding> = {}): SwarmFinding {
  return {
    agent_id: "code-agent",
    task_id: "task-001",
    ts: 1713434400,
    importance: 8,
    category: "security",
    severity: "high",
    summary: "Unvalidated input in endpoint",
    recommendation: "Add Pydantic validation",
    files: ["apps/api/app/routers/admin.py"],
    confidence: 0.9,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminPing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns false when token is null (auth guard)", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPing(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), ERROR_TIMEOUT);
    expect(result.current.data).toBe(false);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("returns true when apiFetch succeeds", async () => {
    mockApiFetch.mockResolvedValue({ ok: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPing(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), ERROR_TIMEOUT);
    expect(result.current.data).toBe(true);
  });

  it("returns false when apiFetch throws (swallows error)", async () => {
    mockApiFetch.mockRejectedValue(new Error("Forbidden"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPing(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), ERROR_TIMEOUT);
    expect(result.current.data).toBe(false);
  });

  it("calls correct URL with auth header", async () => {
    mockApiFetch.mockResolvedValue({ ok: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPing(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith("/api/admin/ping", { token: "test-token" });
  });

  it("uses ['admin', 'ping'] as query key", async () => {
    mockApiFetch.mockResolvedValue({ ok: true });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminPing(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "ping"])).toBe(true);
  });

  it("staleTime is 5 minutes — query not invalidated immediately", async () => {
    mockApiFetch.mockResolvedValue({ ok: true });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminPing(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const state = qc.getQueryState(["admin", "ping"]);
    expect(state?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminStats", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminStats(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("returns AdminStats on success", async () => {
    const stats = makeAdminStats({ total_users: 500, avg_aura_score: null });
    mockApiFetch.mockResolvedValue(stats);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminStats(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total_users).toBe(500);
    expect(result.current.data?.avg_aura_score).toBeNull();
  });

  it("calls /api/admin/stats with token", async () => {
    mockApiFetch.mockResolvedValue(makeAdminStats());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminStats(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith("/api/admin/stats", { token: "test-token" });
  });

  it("uses ['admin', 'stats'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeAdminStats());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "stats"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminUsers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminUsers(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("fetches /api/admin/users with no params", async () => {
    mockApiFetch.mockResolvedValue([makeAdminUserRow()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminUsers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith("/api/admin/users", { token: "test-token" });
  });

  it("builds query string from params", async () => {
    mockApiFetch.mockResolvedValue([makeAdminUserRow()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useAdminUsers({ limit: 20, offset: 40, account_type: "organization" }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const url = mockApiFetch.mock.calls[0][0] as string;
    expect(url).toContain("limit=20");
    expect(url).toContain("offset=40");
    expect(url).toContain("account_type=organization");
  });

  it("uses params in query key for isolation", async () => {
    mockApiFetch.mockResolvedValue([makeAdminUserRow()]);
    const params = { limit: 10, offset: 0 };
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminUsers(params), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "users", params])).toBeDefined();
  });

  it("returns array of AdminUserRow", async () => {
    const users = [
      makeAdminUserRow({ id: "u1", username: "alice" }),
      makeAdminUserRow({ id: "u2", username: "bob", is_platform_admin: true }),
    ];
    mockApiFetch.mockResolvedValue(users);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminUsers(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[1].is_platform_admin).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("usePendingOrganizations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePendingOrganizations(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("calls /api/admin/organizations/pending with token", async () => {
    mockApiFetch.mockResolvedValue([makeAdminOrgRow()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePendingOrganizations(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/organizations/pending",
      { token: "test-token" }
    );
  });

  it("uses ['admin', 'organizations', 'pending'] as query key", async () => {
    mockApiFetch.mockResolvedValue([makeAdminOrgRow()]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => usePendingOrganizations(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "organizations", "pending"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useApproveOrganization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useApproveOrganization(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync("org-123")).rejects.toMatchObject({ status: 401 });
    });
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("calls correct URL with POST method", async () => {
    mockApiFetch.mockResolvedValue({ org_id: "org-123", action: "approved" });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useApproveOrganization(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("org-123");
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/organizations/org-123/approve",
      { token: "test-token", method: "POST" }
    );
  });

  it("invalidates organizations and stats queries on success", async () => {
    mockApiFetch.mockResolvedValue({ org_id: "org-xyz", action: "approved" });
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useApproveOrganization(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("org-xyz");
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["admin", "organizations"] })
    );
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["admin", "stats"] })
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRejectOrganization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls correct URL with POST method", async () => {
    mockApiFetch.mockResolvedValue({ org_id: "org-456", action: "rejected" });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRejectOrganization(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("org-456");
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/organizations/org-456/reject",
      { token: "test-token", method: "POST" }
    );
  });

  it("invalidates organizations and stats on success", async () => {
    mockApiFetch.mockResolvedValue({ org_id: "org-456", action: "rejected" });
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useRejectOrganization(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("org-456");
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["admin", "organizations"] })
    );
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["admin", "stats"] })
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useSwarmAgents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmAgents(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("calls /admin/swarm/agents with token", async () => {
    mockApiFetch.mockResolvedValue({
      agents: [makeSwarmAgent()],
      total_tracked: 1,
      total_untracked: 0,
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmAgents(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith("/admin/swarm/agents", { token: "test-token" });
  });

  it("uses ['admin', 'swarm', 'agents'] as query key", async () => {
    mockApiFetch.mockResolvedValue({ agents: [], total_tracked: 0, total_untracked: 0 });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useSwarmAgents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "swarm", "agents"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useSwarmProposals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmProposals(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("calls /api/admin/swarm/proposals without status filter", async () => {
    mockApiFetch.mockResolvedValue({
      proposals: [makeSwarmProposal()],
      summary: { pending: 1, approved: 0, rejected: 0 },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmProposals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/swarm/proposals",
      { token: "test-token" }
    );
  });

  it("appends status query param when provided", async () => {
    mockApiFetch.mockResolvedValue({
      proposals: [],
      summary: { pending: 0, approved: 5, rejected: 2 },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmProposals("approved"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/swarm/proposals?status=approved",
      { token: "test-token" }
    );
  });

  it("uses status in query key for isolation", async () => {
    mockApiFetch.mockResolvedValue({ proposals: [], summary: { pending: 0, approved: 0, rejected: 0 } });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useSwarmProposals("pending"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "swarm", "proposals", "pending"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDecideProposal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDecideProposal(), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ proposalId: "prop-001", action: "approve" })
      ).rejects.toMatchObject({ status: 401 });
    });
  });

  it("calls correct URL with POST + serialized body", async () => {
    mockApiFetch.mockResolvedValue({ ok: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDecideProposal(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ proposalId: "prop-001", action: "approve" });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/swarm/proposals/prop-001/decide",
      {
        method: "POST",
        body: JSON.stringify({ action: "approve" }),
        token: "test-token",
      }
    );
  });

  it("invalidates swarm proposals cache on success", async () => {
    mockApiFetch.mockResolvedValue({ ok: true });
    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useDecideProposal(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ proposalId: "prop-001", action: "reject" });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["admin", "swarm", "proposals"] })
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminOverview(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("calls /api/admin/stats/overview with token", async () => {
    mockApiFetch.mockResolvedValue(makeAdminOverview());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminOverview(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/stats/overview",
      { token: "test-token" }
    );
  });

  it("returns full AdminOverviewResponse shape", async () => {
    const overview = makeAdminOverview({
      activation_rate_24h: 0.55,
      dau_wau_ratio: 0.4,
      errors_24h: 0,
    });
    mockApiFetch.mockResolvedValue(overview);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminOverview(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.activation_rate_24h).toBe(0.55);
    expect(result.current.data?.presence).toBeDefined();
    expect(result.current.data?.funnels).toBeInstanceOf(Array);
  });

  it("uses ['admin', 'stats', 'overview'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeAdminOverview());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminOverview(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "stats", "overview"])).toBeDefined();
  });

  it("staleTime is 30s — query not invalidated immediately", async () => {
    mockApiFetch.mockResolvedValue(makeAdminOverview());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminOverview(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const state = qc.getQueryState(["admin", "stats", "overview"]);
    expect(state?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminLiveEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminLiveEvents(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("calls correct URL with default limit=50", async () => {
    mockApiFetch.mockResolvedValue([makeActivityEvent()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminLiveEvents(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/events/live?limit=50",
      { token: "test-token" }
    );
  });

  it("uses custom limit in URL and query key", async () => {
    mockApiFetch.mockResolvedValue([makeActivityEvent()]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminLiveEvents(20), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/events/live?limit=20",
      { token: "test-token" }
    );
    expect(qc.getQueryData(["admin", "events", "live", 20])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useSwarmFindings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("throws ApiError 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmFindings(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
  });

  it("calls /api/admin/swarm/findings with no filters", async () => {
    mockApiFetch.mockResolvedValue({ findings: [makeSwarmFinding()], total: 1, db_exists: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmFindings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/admin/swarm/findings",
      { token: "test-token" }
    );
  });

  it("appends category and min_importance to query string", async () => {
    mockApiFetch.mockResolvedValue({ findings: [], total: 0, db_exists: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSwarmFindings("security", 7), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const url = mockApiFetch.mock.calls[0][0] as string;
    expect(url).toContain("category=security");
    expect(url).toContain("min_importance=7");
  });

  it("uses category + minImportance in query key for isolation", async () => {
    mockApiFetch.mockResolvedValue({ findings: [], total: 0, db_exists: true });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useSwarmFindings("performance", 5), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["admin", "swarm", "findings", "performance", 5])).toBeDefined();
  });
});
