import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiError, apiFetch } from "./client";

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: "mock-token" } },
      }),
    },
  }),
}));

describe("ApiError", () => {
  it("sets status, code, and detail", () => {
    const err = new ApiError(404, "NOT_FOUND", "Profile not found");
    expect(err.status).toBe(404);
    expect(err.code).toBe("NOT_FOUND");
    expect(err.detail).toBe("Profile not found");
    expect(err.message).toBe("Profile not found");
    expect(err.name).toBe("ApiError");
  });

  it("is an instance of Error", () => {
    const err = new ApiError(500, "INTERNAL", "Server error");
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(ApiError);
  });
});

describe("apiFetch", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("unwraps envelope response", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ data: { id: 1 }, meta: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const result = await apiFetch("/test");
    expect(result).toEqual({ id: 1 });
  });

  it("returns raw response when no envelope", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const result = await apiFetch("/health");
    expect(result).toEqual({ status: "ok" });
  });

  it("normalizes double /api/ prefix", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ data: null }), { status: 200 }),
    );
    await apiFetch("/api/test");
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/test",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("throws ApiError on non-ok response with error body", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({ error: { code: "NOT_FOUND", message: "Not found" } }),
        { status: 404, statusText: "Not Found" },
      ),
    );
    await expect(apiFetch("/missing")).rejects.toThrow(ApiError);
    try {
      await apiFetch("/missing");
    } catch (e) {
      // re-mock for this catch
    }
  });

  it("throws ApiError with UNKNOWN code when response body is not JSON", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response("Internal Server Error", {
        status: 500,
        statusText: "Internal Server Error",
      }),
    );
    try {
      await apiFetch("/broken");
      expect.unreachable("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).code).toBe("UNKNOWN");
    }
  });

  it("uses explicit token when provided", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ data: {} }), { status: 200 }),
    );
    await apiFetch("/test", { token: "explicit-token" });
    const callHeaders = fetchSpy.mock.calls[0][1]?.headers as Record<string, string>;
    expect(callHeaders.Authorization).toBe("Bearer explicit-token");
  });

  it("merges extra headers", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ data: {} }), { status: 200 }),
    );
    await apiFetch("/test", { headers: { "X-Custom": "value" } });
    const callHeaders = fetchSpy.mock.calls[0][1]?.headers as Record<string, string>;
    expect(callHeaders["X-Custom"]).toBe("value");
    expect(callHeaders["Content-Type"]).toBe("application/json");
  });

  it("passes through fetch options like method and body", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ data: { created: true } }), { status: 201 }),
    );
    await apiFetch("/items", {
      method: "POST",
      body: JSON.stringify({ name: "test" }),
    });
    expect(fetchSpy.mock.calls[0][1]?.method).toBe("POST");
    expect(fetchSpy.mock.calls[0][1]?.body).toBe(JSON.stringify({ name: "test" }));
  });

  it("handles detail-style error body", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({ detail: { code: "FORBIDDEN", message: "No access" } }),
        { status: 403, statusText: "Forbidden" },
      ),
    );
    try {
      await apiFetch("/admin");
      expect.unreachable("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).code).toBe("FORBIDDEN");
      expect((e as ApiError).detail).toBe("No access");
    }
  });
});
