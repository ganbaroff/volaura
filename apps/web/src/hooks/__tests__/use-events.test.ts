import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Generated SDK mocks (before any imports) ──────────────────────────────────

const mockListEvents = vi.fn();
const mockGetEvent = vi.fn();
const mockCreateEvent = vi.fn();
const mockRegisterForEvent = vi.fn();
const mockMyRegistrations = vi.fn();

vi.mock("@/lib/api/generated", () => ({
  listEventsApiEventsGet: (...args: unknown[]) => mockListEvents(...args),
  getEventApiEventsEventIdGet: (...args: unknown[]) => mockGetEvent(...args),
  createEventApiEventsPost: (...args: unknown[]) => mockCreateEvent(...args),
  registerForEventApiEventsEventIdRegisterPost: (...args: unknown[]) => mockRegisterForEvent(...args),
  myRegistrationsApiEventsMyRegistrationsGet: (...args: unknown[]) => mockMyRegistrations(...args),
}));

// ── apiFetch mock ─────────────────────────────────────────────────────────────

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
  toApiError: (
    error: { code?: string; message?: string } | undefined,
    fallback?: { message?: string }
  ) =>
    new Error(error?.message ?? fallback?.message ?? "Unknown error"),
}));

// ── useAuthToken mock ─────────────────────────────────────────────────────────

const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import {
  useEvents,
  useEvent,
  useMyEventTimeline,
  useMyEvents,
  useMyOwnedEvents,
  useRateProfessional,
  useEventAttendees,
  useCreateEvent,
  useRegisterForEvent,
} from "../queries/use-events";
import type { EventAttendeeRow } from "../queries/use-events";

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

function makeEventResponse(overrides: Record<string, unknown> = {}) {
  return {
    id: "event_001",
    title: "Test Event",
    description: "A test event",
    status: "upcoming",
    start_time: "2026-05-01T10:00:00Z",
    end_time: "2026-05-01T12:00:00Z",
    created_at: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

function makeAttendee(overrides: Partial<EventAttendeeRow> = {}): EventAttendeeRow {
  return {
    registration_id: "reg_001",
    professional_id: "prof_001",
    status: "registered",
    registered_at: "2026-04-10T00:00:00Z",
    checked_in_at: null,
    display_name: "John Doe",
    username: "johndoe",
    total_score: 85.0,
    badge_tier: "gold",
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns events array on success via SDK", async () => {
    const events = [makeEventResponse({ id: "e1" }), makeEventResponse({ id: "e2" })];
    mockListEvents.mockResolvedValue({ data: events, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEvents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
  });

  it("calls SDK with status and limit params", async () => {
    mockListEvents.mockResolvedValue({ data: [], error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useEvents({ status: "upcoming", limit: 10, offset: 0 }),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockListEvents).toHaveBeenCalledWith({
      query: { status: "upcoming", limit: 10, offset: 0 },
    });
  });

  it("throws when SDK returns error", async () => {
    mockListEvents.mockResolvedValue({
      data: null,
      error: { code: "RATE_LIMITED", message: "Event list temporarily unavailable" },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEvents(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Event list temporarily unavailable");
  });

  it("uses ['events', params] as query key", async () => {
    mockListEvents.mockResolvedValue({ data: [], error: null });
    const { wrapper, qc } = makeWrapper();

    const params = { status: "active" };
    const { result } = renderHook(() => useEvents(params), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["events", params])).toBeDefined();
  });

  it("staleTime is 2 minutes — query not stale immediately", async () => {
    mockListEvents.mockResolvedValue({ data: [], error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useEvents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["events", undefined])?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not fetch when eventId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useEvent(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetEvent).not.toHaveBeenCalled();
  });

  it("fetches event by ID via SDK", async () => {
    const event = makeEventResponse({ id: "event_abc" });
    mockGetEvent.mockResolvedValue({ data: event, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEvent("event_abc"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetEvent).toHaveBeenCalledWith({ path: { event_id: "event_abc" } });
  });

  it("throws when SDK returns error or null data", async () => {
    mockGetEvent.mockResolvedValue({
      data: null,
      error: { code: "EVENT_NOT_FOUND", message: "Event not found" },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEvent("event_missing"), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Event not found");
  });

  it("uses ['events', eventId] as query key", async () => {
    mockGetEvent.mockResolvedValue({ data: makeEventResponse({ id: "event_key" }), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useEvent("event_key"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["events", "event_key"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyEventTimeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns my timeline events array via apiFetch", async () => {
    const events = [makeEventResponse({ id: "my_event_1" })];
    mockApiFetch.mockResolvedValue(events);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyEventTimeline(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
  });

  it("calls apiFetch with /events/my/timeline and auth token", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyEventTimeline(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/events/my/timeline", { token: "test-token" });
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyEventTimeline(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  it("uses ['events', 'my', 'timeline'] as query key", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyEventTimeline(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["events", "my", "timeline"])).toBeDefined();
  });

  it("keeps useMyEvents as a backward-compatible alias", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyEvents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/events/my/timeline", { token: "test-token" });
  });
});

describe("useMyOwnedEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns owned events array via apiFetch", async () => {
    const events = [makeEventResponse({ id: "owned_event_1" })];
    mockApiFetch.mockResolvedValue(events);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyOwnedEvents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
  });

  it("calls apiFetch with /events/my/owned and auth token", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyOwnedEvents(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/events/my/owned", { token: "test-token" });
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRateProfessional", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls POST /api/events/{id}/rate/coordinator", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRateProfessional("event_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        registration_id: "reg_001",
        rating: 4,
        feedback: "Great job",
      });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/events/event_001/rate/coordinator",
      expect.objectContaining({ method: "POST", token: "test-token" })
    );
  });

  it("invalidates attendees cache on success", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["events", "event_001", "attendees"], [makeAttendee()]);

    const { result } = renderHook(() => useRateProfessional("event_001"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ registration_id: "reg_001", rating: 5 });
    });

    expect(qc.getQueryState(["events", "event_001", "attendees"])?.isInvalidated).toBe(true);
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRateProfessional("event_001"), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({ registration_id: "reg_001", rating: 3 });
      })
    ).rejects.toThrow();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useEventAttendees", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("does not fetch when eventId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useEventAttendees(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("returns attendees list on success", async () => {
    const attendees = [makeAttendee({ registration_id: "reg_001" })];
    mockApiFetch.mockResolvedValue(attendees);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventAttendees("event_001"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
  });

  it("calls apiFetch with correct URL and token", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventAttendees("event_xyz"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/events/event_xyz/attendees",
      { token: "test-token" }
    );
  });

  it("throwOnError is false — errors set isError, not throw", async () => {
    mockApiFetch.mockRejectedValue(new Error("Forbidden"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useEventAttendees("event_001"), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    // throwOnError: false means the component doesn't crash
    expect(result.current.error).toBeDefined();
  });

  it("uses ['events', eventId, 'attendees'] as query key", async () => {
    mockApiFetch.mockResolvedValue([]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useEventAttendees("event_key"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["events", "event_key", "attendees"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useCreateEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates event via SDK and invalidates events cache", async () => {
    const newEvent = makeEventResponse({ id: "new_event" });
    mockCreateEvent.mockResolvedValue({ data: newEvent, error: null });
    const { wrapper, qc } = makeWrapper();

    // Pre-populate the ["events"] key directly so invalidation can be observed
    qc.setQueryData(["events"], [makeEventResponse()]);

    const { result } = renderHook(() => useCreateEvent(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        title: "New Event",
        description: "Test",
        start_time: "2026-06-01T10:00:00Z",
        end_time: "2026-06-01T12:00:00Z",
      } as unknown as Parameters<typeof result.current.mutateAsync>[0]);
    });

    expect(qc.getQueryState(["events"])?.isInvalidated).toBe(true);
  });

  it("throws when SDK returns error", async () => {
    mockCreateEvent.mockResolvedValue({
      data: null,
      error: { code: "VALIDATION_ERROR", message: "Title is required" },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCreateEvent(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({
          title: "Bad Event",
        } as unknown as Parameters<typeof result.current.mutateAsync>[0]);
      })
    ).rejects.toThrow("Title is required");
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRegisterForEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("registers for event via SDK and invalidates event cache", async () => {
    const registration = { id: "reg_001", status: "registered" };
    mockRegisterForEvent.mockResolvedValue({ data: registration, error: null });
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["events", "event_001"], makeEventResponse());

    const { result } = renderHook(() => useRegisterForEvent(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ eventId: "event_001" });
    });

    expect(qc.getQueryState(["events", "event_001"])?.isInvalidated).toBe(true);
  });

  it("calls SDK with correct event_id path param", async () => {
    mockRegisterForEvent.mockResolvedValue({ data: { id: "reg_002", status: "registered" }, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRegisterForEvent(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ eventId: "event_special" });
    });

    expect(mockRegisterForEvent).toHaveBeenCalledWith({
      path: { event_id: "event_special" },
    });
  });

  it("throws when SDK returns error", async () => {
    mockRegisterForEvent.mockResolvedValue({
      data: null,
      error: { code: "EVENT_CLOSED", message: "Registration is closed" },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRegisterForEvent(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({ eventId: "event_closed" });
      })
    ).rejects.toThrow("Registration is closed");
  });
});
