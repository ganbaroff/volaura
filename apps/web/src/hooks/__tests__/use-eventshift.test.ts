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
  useEventShiftActivation,
  useEventShiftEvents,
  useEventShiftEvent,
  useCreateEventShiftEvent,
  useDepartments,
  useCreateDepartment,
  useDepartmentBlueprint,
  useDepartmentBlueprintSection,
  useAreas,
  useCreateArea,
  useUnits,
  useCreateUnit,
  useAssignments,
  useCreateAssignment,
  useMetrics,
  useRecordMetric,
} from "../queries/use-eventshift";

import type {
  EventShiftEvent,
  EventShiftDepartment,
  EventShiftArea,
  EventShiftUnit,
  EventShiftAssignment,
  EventShiftMetric,
  ActivationState,
  DepartmentBlueprint,
  DepartmentBlueprintSection,
  EventShiftEventCreate,
  DepartmentCreate,
  AreaCreate,
  UnitCreatePayload,
  AssignmentCreate,
  MetricCreate,
} from "../queries/use-eventshift";

// ── Helpers ───────────────────────────────────────────────────────────────────

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

function makeActivationState(overrides: Partial<ActivationState> = {}): ActivationState {
  return {
    org_id: "org_001",
    module_slug: "eventshift",
    active: true,
    ...overrides,
  };
}

function makeEvent(overrides: Partial<EventShiftEvent> = {}): EventShiftEvent {
  return {
    id: "evt_001",
    org_id: "org_001",
    slug: "annual-gala",
    name: "Annual Gala",
    description: null,
    start_at: "2026-06-01T18:00:00Z",
    end_at: "2026-06-01T23:00:00Z",
    timezone: "Asia/Baku",
    location: null,
    metadata: null,
    status: "planning",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeDepartment(overrides: Partial<EventShiftDepartment> = {}): EventShiftDepartment {
  return {
    id: "dept_001",
    org_id: "org_001",
    event_id: "evt_001",
    name: "Logistics",
    description: null,
    color_hex: null,
    lead_user_id: null,
    sort_order: 0,
    metadata: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeBlueprint(overrides: Partial<DepartmentBlueprint> = {}): DepartmentBlueprint {
  return {
    department_id: "dept_001",
    blueprint: { sections: ["overview", "tasks"] },
    ...overrides,
  };
}

function makeBlueprintSection(overrides: Partial<DepartmentBlueprintSection> = {}): DepartmentBlueprintSection {
  return {
    department_id: "dept_001",
    section: "overview",
    data: { title: "Overview", content: "..." },
    ...overrides,
  };
}

function makeArea(overrides: Partial<EventShiftArea> = {}): EventShiftArea {
  return {
    id: "area_001",
    org_id: "org_001",
    department_id: "dept_001",
    name: "Zone A",
    description: null,
    location: null,
    metadata: null,
    coordinator_user_id: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeUnit(overrides: Partial<EventShiftUnit> = {}): EventShiftUnit {
  return {
    id: "unit_001",
    org_id: "org_001",
    area_id: "area_001",
    name: "Shift A-1",
    description: null,
    shift_start: "2026-06-01T18:00:00Z",
    shift_end: "2026-06-01T22:00:00Z",
    required_headcount: 5,
    required_skills: [],
    status: "open",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeAssignment(overrides: Partial<EventShiftAssignment> = {}): EventShiftAssignment {
  return {
    id: "asgn_001",
    org_id: "org_001",
    unit_id: "unit_001",
    user_id: "user_001",
    role: "staff",
    status: "assigned",
    notes: null,
    assigned_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeMetric(overrides: Partial<EventShiftMetric> = {}): EventShiftMetric {
  return {
    id: "metric_001",
    org_id: "org_001",
    unit_id: "unit_001",
    metric_type: "attendance",
    value: 42,
    payload: null,
    recorded_at: "2026-06-01T22:00:00Z",
    recorded_by: null,
    created_at: "2026-06-01T22:00:00Z",
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useEventShiftActivation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns activation state on success", async () => {
    mockApiFetch.mockResolvedValue(makeActivationState());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftActivation(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.active).toBe(true);
    expect(result.current.data?.module_slug).toBe("eventshift");
  });

  it("fetches correct URL", async () => {
    mockApiFetch.mockResolvedValue(makeActivationState());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftActivation(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/debug/activation-state",
      { token: "test-token" },
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftActivation(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("uses ['eventshift', 'activation'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeActivationState());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useEventShiftActivation(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "activation"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useEventShiftEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("fetches all events without status filter", async () => {
    mockApiFetch.mockResolvedValue([makeEvent()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvents(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/events",
      { token: "test-token" },
    );
  });

  it("appends status query param when status provided", async () => {
    mockApiFetch.mockResolvedValue([makeEvent({ status: "live" })]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvents("live"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/events?status=live",
      { token: "test-token" },
    );
  });

  it("uses 'all' in cache key when no status", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "events", "all"])).toBeDefined();
  });

  it("uses status in cache key when status provided", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvents("planning"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "events", "planning"])).toBeDefined();
  });

  it("keeps distinct caches for different statuses", async () => {
    mockApiFetch
      .mockResolvedValueOnce([makeEvent({ status: "live" })])
      .mockResolvedValueOnce([makeEvent({ status: "closed" })]);
    const { wrapper, qc } = makeWrapper();

    const { result: r1 } = renderHook(() => useEventShiftEvents("live"), { wrapper });
    const { result: r2 } = renderHook(() => useEventShiftEvents("closed"), { wrapper });

    await waitFor(() => expect(r1.current.isSuccess).toBe(true));
    await waitFor(() => expect(r2.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "events", "live"])).toBeDefined();
    expect(qc.getQueryData(["eventshift", "events", "closed"])).toBeDefined();
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvents(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useEventShiftEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when eventId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useEventShiftEvent(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL when eventId provided", async () => {
    mockApiFetch.mockResolvedValue(makeEvent({ id: "evt_xyz" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvent("evt_xyz"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/events/evt_xyz",
      { token: "test-token" },
    );
  });

  it("returns event data on success", async () => {
    const event = makeEvent({ id: "evt_abc", name: "Tech Summit" });
    mockApiFetch.mockResolvedValue(event);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvent("evt_abc"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe("evt_abc");
    expect(result.current.data?.name).toBe("Tech Summit");
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventShiftEvent("evt_noauth"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateEventShiftEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("POSTs to correct URL with JSON body", async () => {
    const newEvent = makeEvent({ slug: "new-event" });
    mockApiFetch.mockResolvedValue(newEvent);
    const { wrapper } = makeWrapper();

    const payload: EventShiftEventCreate = {
      slug: "new-event",
      name: "New Event",
      start_at: "2026-07-01T10:00:00Z",
      end_at: "2026-07-01T20:00:00Z",
    };

    const { result } = renderHook(() => useCreateEventShiftEvent(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/events",
      expect.objectContaining({
        method: "POST",
        token: "test-token",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("invalidates ['eventshift', 'events'] on success", async () => {
    mockApiFetch.mockResolvedValue(makeEvent());
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateEventShiftEvent(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        slug: "slug",
        name: "name",
        start_at: "2026-07-01T10:00:00Z",
        end_at: "2026-07-01T20:00:00Z",
      });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["eventshift", "events"] }),
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateEventShiftEvent(), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({
          slug: "s",
          name: "n",
          start_at: "2026-07-01T10:00:00Z",
          end_at: "2026-07-01T20:00:00Z",
        }),
      ).rejects.toMatchObject({ status: 401 });
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDepartments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when eventId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useDepartments(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL when eventId provided", async () => {
    mockApiFetch.mockResolvedValue([makeDepartment()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDepartments("evt_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/events/evt_001/departments",
      { token: "test-token" },
    );
  });

  it("uses eventId in cache key", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useDepartments("evt_001"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "departments", "evt_001"])).toBeDefined();
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDepartments("evt_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateDepartment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("POSTs to correct URL with JSON body", async () => {
    mockApiFetch.mockResolvedValue(makeDepartment({ name: "Security" }));
    const { wrapper } = makeWrapper();

    const payload: DepartmentCreate = { name: "Security" };

    const { result } = renderHook(() => useCreateDepartment("evt_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/events/evt_001/departments",
      expect.objectContaining({
        method: "POST",
        token: "test-token",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("invalidates ['eventshift', 'departments', eventId] on success", async () => {
    mockApiFetch.mockResolvedValue(makeDepartment());
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateDepartment("evt_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ name: "Security" });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["eventshift", "departments", "evt_001"] }),
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateDepartment("evt_001"), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ name: "Security" }),
      ).rejects.toMatchObject({ status: 401 });
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDepartmentBlueprint", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when departmentId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useDepartmentBlueprint(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL when departmentId provided", async () => {
    mockApiFetch.mockResolvedValue(makeBlueprint());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDepartmentBlueprint("dept_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/departments/dept_001/blueprint",
      { token: "test-token" },
    );
  });

  it("returns blueprint data on success", async () => {
    const blueprint = makeBlueprint({ department_id: "dept_xyz" });
    mockApiFetch.mockResolvedValue(blueprint);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDepartmentBlueprint("dept_xyz"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.department_id).toBe("dept_xyz");
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDepartmentBlueprint("dept_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDepartmentBlueprintSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when departmentId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(
      () => useDepartmentBlueprintSection(undefined, "overview"),
      { wrapper },
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("does not fetch when section is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(
      () => useDepartmentBlueprintSection("dept_001", undefined),
      { wrapper },
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("does not fetch when both params are undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(
      () => useDepartmentBlueprintSection(undefined, undefined),
      { wrapper },
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL with section query param when both params provided", async () => {
    mockApiFetch.mockResolvedValue(makeBlueprintSection());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useDepartmentBlueprintSection("dept_001", "overview"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/departments/dept_001/blueprint?section=overview",
      { token: "test-token" },
    );
  });

  it("includes both params in cache key", async () => {
    mockApiFetch.mockResolvedValue(makeBlueprintSection());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(
      () => useDepartmentBlueprintSection("dept_001", "tasks"),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(
      qc.getQueryData(["eventshift", "blueprint", "dept_001", "tasks"]),
    ).toBeDefined();
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useDepartmentBlueprintSection("dept_001", "overview"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAreas", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when departmentId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAreas(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL when departmentId provided", async () => {
    mockApiFetch.mockResolvedValue([makeArea()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAreas("dept_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/departments/dept_001/areas",
      { token: "test-token" },
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAreas("dept_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateArea", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("POSTs to correct URL with JSON body", async () => {
    mockApiFetch.mockResolvedValue(makeArea({ name: "Zone B" }));
    const { wrapper } = makeWrapper();

    const payload: AreaCreate = { name: "Zone B" };

    const { result } = renderHook(() => useCreateArea("dept_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/departments/dept_001/areas",
      expect.objectContaining({
        method: "POST",
        token: "test-token",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("invalidates ['eventshift', 'areas', departmentId] on success", async () => {
    mockApiFetch.mockResolvedValue(makeArea());
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateArea("dept_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ name: "Zone B" });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["eventshift", "areas", "dept_001"] }),
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateArea("dept_001"), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ name: "Zone B" }),
      ).rejects.toMatchObject({ status: 401 });
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useUnits", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when areaId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useUnits(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL when areaId provided", async () => {
    mockApiFetch.mockResolvedValue([makeUnit()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUnits("area_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/areas/area_001/units",
      { token: "test-token" },
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUnits("area_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateUnit", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("POSTs to correct URL with JSON body", async () => {
    mockApiFetch.mockResolvedValue(makeUnit({ name: "Shift B-1" }));
    const { wrapper } = makeWrapper();

    const payload: UnitCreatePayload = {
      name: "Shift B-1",
      shift_start: "2026-06-01T18:00:00Z",
      shift_end: "2026-06-01T22:00:00Z",
    };

    const { result } = renderHook(() => useCreateUnit("area_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/areas/area_001/units",
      expect.objectContaining({
        method: "POST",
        token: "test-token",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("invalidates ['eventshift', 'units', areaId] on success", async () => {
    mockApiFetch.mockResolvedValue(makeUnit());
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateUnit("area_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        name: "Shift B-1",
        shift_start: "2026-06-01T18:00:00Z",
        shift_end: "2026-06-01T22:00:00Z",
      });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["eventshift", "units", "area_001"] }),
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateUnit("area_001"), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({
          name: "Shift B-1",
          shift_start: "2026-06-01T18:00:00Z",
          shift_end: "2026-06-01T22:00:00Z",
        }),
      ).rejects.toMatchObject({ status: 401 });
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAssignments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when unitId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAssignments(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches correct URL when unitId provided", async () => {
    mockApiFetch.mockResolvedValue([makeAssignment()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssignments("unit_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/units/unit_001/assignments",
      { token: "test-token" },
    );
  });

  it("returns assignment list on success", async () => {
    const assignment = makeAssignment({ role: "lead", status: "accepted" });
    mockApiFetch.mockResolvedValue([assignment]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssignments("unit_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.[0].role).toBe("lead");
    expect(result.current.data?.[0].status).toBe("accepted");
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssignments("unit_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateAssignment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("POSTs to correct URL with JSON body", async () => {
    mockApiFetch.mockResolvedValue(makeAssignment());
    const { wrapper } = makeWrapper();

    const payload: AssignmentCreate = { user_id: "user_002", role: "lead" };

    const { result } = renderHook(() => useCreateAssignment("unit_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/units/unit_001/assignments",
      expect.objectContaining({
        method: "POST",
        token: "test-token",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("invalidates ['eventshift', 'assignments', unitId] on success", async () => {
    mockApiFetch.mockResolvedValue(makeAssignment());
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useCreateAssignment("unit_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ user_id: "user_002" });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["eventshift", "assignments", "unit_001"] }),
    );
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateAssignment("unit_001"), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ user_id: "user_002" }),
      ).rejects.toMatchObject({ status: 401 });
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMetrics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when unitId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useMetrics(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches all metrics without type filter", async () => {
    mockApiFetch.mockResolvedValue([makeMetric()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMetrics("unit_001"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/units/unit_001/metrics",
      { token: "test-token" },
    );
  });

  it("appends metric_type query param when provided", async () => {
    mockApiFetch.mockResolvedValue([makeMetric({ metric_type: "attendance" })]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMetrics("unit_001", "attendance"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/units/unit_001/metrics?metric_type=attendance",
      { token: "test-token" },
    );
  });

  it("uses 'all' in cache key when no metric_type", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMetrics("unit_001"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "metrics", "unit_001", "all"])).toBeDefined();
  });

  it("uses metric_type in cache key when provided", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(
      () => useMetrics("unit_001", "incident"),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(
      qc.getQueryData(["eventshift", "metrics", "unit_001", "incident"]),
    ).toBeDefined();
  });

  it("keeps distinct caches for different metric types", async () => {
    mockApiFetch
      .mockResolvedValueOnce([makeMetric({ metric_type: "attendance" })])
      .mockResolvedValueOnce([makeMetric({ metric_type: "incident" })]);
    const { wrapper, qc } = makeWrapper();

    const { result: r1 } = renderHook(() => useMetrics("unit_001", "attendance"), { wrapper });
    const { result: r2 } = renderHook(() => useMetrics("unit_001", "incident"), { wrapper });

    await waitFor(() => expect(r1.current.isSuccess).toBe(true));
    await waitFor(() => expect(r2.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["eventshift", "metrics", "unit_001", "attendance"])).toBeDefined();
    expect(qc.getQueryData(["eventshift", "metrics", "unit_001", "incident"])).toBeDefined();
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMetrics("unit_001"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRecordMetric", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("POSTs to correct URL with JSON body", async () => {
    mockApiFetch.mockResolvedValue(makeMetric());
    const { wrapper } = makeWrapper();

    const payload: MetricCreate = {
      metric_type: "attendance",
      value: 47,
    };

    const { result } = renderHook(() => useRecordMetric("unit_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync(payload);
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/eventshift/units/unit_001/metrics",
      expect.objectContaining({
        method: "POST",
        token: "test-token",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("invalidates ['eventshift', 'metrics', unitId] on success", async () => {
    mockApiFetch.mockResolvedValue(makeMetric());
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useRecordMetric("unit_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ metric_type: "attendance", value: 47 });
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["eventshift", "metrics", "unit_001"] }),
    );
  });

  it("returns recorded metric data on success", async () => {
    const metric = makeMetric({ metric_type: "reliability_proof", value: 1 });
    mockApiFetch.mockResolvedValue(metric);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRecordMetric("unit_001"), { wrapper });

    let data: EventShiftMetric | undefined;
    await act(async () => {
      data = await result.current.mutateAsync({
        metric_type: "reliability_proof",
        value: 1,
      });
    });

    expect(data?.metric_type).toBe("reliability_proof");
    expect(data?.value).toBe(1);
  });

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRecordMetric("unit_001"), { wrapper });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ metric_type: "attendance" }),
      ).rejects.toMatchObject({ status: 401 });
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});
