import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";

// ── posthog mock ──────────────────────────────────────────────────────────────
// vi.mock factories are hoisted before imports, so we must use vi.hoisted()
// to declare variables that factory closures can reference safely.
const { mockPosthogCapture } = vi.hoisted(() => ({
  mockPosthogCapture: vi.fn(),
}));

vi.mock("posthog-js", () => ({
  default: {
    __loaded: true,
    capture: mockPosthogCapture,
  },
}));

// ── API client mock (API_BASE) ────────────────────────────────────────────────
vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  };
});

// ── useAuthToken mock ─────────────────────────────────────────────────────────
const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── fetch mock ────────────────────────────────────────────────────────────────
const mockFetch = vi.fn();

// ── Import (after mocks) ──────────────────────────────────────────────────────
import { useTrackEvent } from "../use-analytics";
import posthog from "posthog-js";

// ─────────────────────────────────────────────────────────────────────────────

// Helper — cast posthog to a mutable object so tests can toggle __loaded
const posthogMock = posthog as unknown as { __loaded: boolean; capture: ReturnType<typeof vi.fn> };

describe("useTrackEvent", () => {
  const originalFetch = globalThis.fetch;
  const originalLocation = globalThis.window?.location;

  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.fetch = mockFetch;
    mockFetch.mockResolvedValue(new Response("{}", { status: 200 }));
    posthogMock.__loaded = true;

    // Default: authenticated
    mockGetToken.mockResolvedValue("tok_test");

    // Default pathname
    Object.defineProperty(window, "location", {
      value: { pathname: "/en/dashboard" },
      writable: true,
    });
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    if (originalLocation !== undefined) {
      Object.defineProperty(window, "location", {
        value: originalLocation,
        writable: true,
      });
    }
  });

  // ── Locale extraction ────────────────────────────────────────────────────

  it("extracts locale from window.location.pathname (/az/dashboard → az)", async () => {
    Object.defineProperty(window, "location", {
      value: { pathname: "/az/dashboard" },
      writable: true,
    });

    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.locale).toBe("az");
  });

  it("extracts locale from /en/... path", async () => {
    Object.defineProperty(window, "location", {
      value: { pathname: "/en/profile" },
      writable: true,
    });

    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.locale).toBe("en");
  });

  it("falls back to 'en' when pathname is root '/'", async () => {
    Object.defineProperty(window, "location", {
      value: { pathname: "/" },
      writable: true,
    });

    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.locale).toBe("en");
  });

  // ── Payload shape ────────────────────────────────────────────────────────

  it("sends correct payload shape to /api/analytics/event", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("assessment_started", { step: 1 }, "sess_abc");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/analytics/event",
      expect.objectContaining({
        method: "POST",
        body: expect.any(String),
      })
    );

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body).toMatchObject({
      event_name: "assessment_started",
      properties: { step: 1 },
      session_id: "sess_abc",
      locale: "en",
      platform: "web",
    });
  });

  it("includes Authorization header with Bearer token", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer tok_test");
  });

  it("includes Content-Type application/json header", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("passes platform: 'web' in payload", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("page_view");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.platform).toBe("web");
  });

  it("uses empty object for properties when not provided", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.properties).toEqual({});
  });

  it("passes sessionId when provided", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event", {}, "session_xyz");

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.session_id).toBe("session_xyz");
  });

  it("passes undefined session_id when sessionId not provided", async () => {
    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event", { foo: "bar" });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.session_id).toBeUndefined();
  });

  // ── Auth guard ───────────────────────────────────────────────────────────

  it("skips API call silently when getToken returns null", async () => {
    mockGetToken.mockResolvedValue(null);

    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    expect(mockFetch).not.toHaveBeenCalled();
  });

  // ── PostHog ──────────────────────────────────────────────────────────────

  it("calls posthog.capture when posthog.__loaded is true", async () => {
    posthogMock.__loaded = true;

    const { result } = renderHook(() => useTrackEvent());
    await result.current("assessment_started", { step: 1 }, "sess_abc");

    expect(mockPosthogCapture).toHaveBeenCalledWith(
      "assessment_started",
      expect.objectContaining({
        step: 1,
        locale: "en",
        session_id: "sess_abc",
      })
    );
  });

  it("skips posthog.capture when posthog.__loaded is false", async () => {
    posthogMock.__loaded = false;

    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    expect(mockPosthogCapture).not.toHaveBeenCalled();
  });

  // ── Error resilience ─────────────────────────────────────────────────────

  it("never throws even if fetch fails", async () => {
    mockFetch.mockRejectedValue(new Error("network failure"));

    const { result } = renderHook(() => useTrackEvent());

    await expect(result.current("test_event")).resolves.toBeUndefined();
  });

  it("never throws even if posthog.capture throws", async () => {
    posthogMock.__loaded = true;
    mockPosthogCapture.mockImplementation(() => {
      throw new Error("posthog crash");
    });

    const { result } = renderHook(() => useTrackEvent());

    await expect(result.current("test_event")).resolves.toBeUndefined();
  });

  it("still calls posthog even when fetch fails", async () => {
    mockFetch.mockRejectedValue(new Error("network failure"));
    posthogMock.__loaded = true;

    const { result } = renderHook(() => useTrackEvent());
    await result.current("test_event");

    expect(mockPosthogCapture).toHaveBeenCalledOnce();
  });

  // ── Hook identity ────────────────────────────────────────────────────────

  it("returns a stable callback reference across re-renders", () => {
    const { result, rerender } = renderHook(() => useTrackEvent());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
