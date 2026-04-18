import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

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
}));

const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import { useSkill } from "../queries/use-skill";
import type { SkillResponse } from "../queries/use-skill";

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

function makeSkillResponse(overrides: Partial<SkillResponse> = {}): SkillResponse {
  return {
    skill: "communication-coach",
    output: { advice: "Speak clearly and listen actively." },
    model_used: "gemini-2.5-flash",
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useSkill", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  // ── POST method ───────────────────────────────────────────────────────────

  it("calls POST method on apiFetch", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("communication-coach"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/skills/communication-coach",
      expect.objectContaining({ method: "POST" })
    );
  });

  // ── skillName in URL ──────────────────────────────────────────────────────

  it("includes skillName in the URL path", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse({ skill: "leadership-advisor" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("leadership-advisor"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/skills/leadership-advisor",
      expect.any(Object)
    );
  });

  // ── default language "en" body ────────────────────────────────────────────

  it("sends default body {language: 'en'} when no request provided", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("any-skill"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/skills/any-skill",
      expect.objectContaining({ body: JSON.stringify({ language: "en" }) })
    );
  });

  // ── request body passed through ────────────────────────────────────────────

  it("sends custom request body when provided", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse());
    const { wrapper } = makeWrapper();

    const request = { context: { topic: "leadership" }, language: "az" };

    const { result } = renderHook(
      () => useSkill("leadership-advisor", request),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/skills/leadership-advisor",
      expect.objectContaining({ body: JSON.stringify(request) })
    );
  });

  // ── auth guard ────────────────────────────────────────────────────────────

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("communication-coach"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  // ── enabled option ────────────────────────────────────────────────────────

  it("does not fetch when enabled=false", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(
      () => useSkill("communication-coach", undefined, { enabled: false }),
      { wrapper }
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches when enabled=true (default)", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("communication-coach"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalled();
  });

  // ── staleTime override ────────────────────────────────────────────────────

  it("uses default staleTime of 5 minutes when not overridden", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("communication-coach"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["skill", "communication-coach", undefined])?.isInvalidated).toBe(false);
  });

  // ── cache key ─────────────────────────────────────────────────────────────

  it("uses ['skill', skillName, request] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeSkillResponse());
    const { wrapper, qc } = makeWrapper();

    const request = { language: "en" };
    const { result } = renderHook(
      () => useSkill("communication-coach", request),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["skill", "communication-coach", request])).toBeDefined();
  });

  it("distinct cache keys for different skillNames", async () => {
    mockApiFetch
      .mockResolvedValueOnce(makeSkillResponse({ skill: "skill-a" }))
      .mockResolvedValueOnce(makeSkillResponse({ skill: "skill-b" }));

    const { wrapper, qc } = makeWrapper();

    const { result: r1 } = renderHook(() => useSkill("skill-a"), { wrapper });
    const { result: r2 } = renderHook(() => useSkill("skill-b"), { wrapper });

    await waitFor(() => expect(r1.current.isSuccess).toBe(true));
    await waitFor(() => expect(r2.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["skill", "skill-a", undefined])).toBeDefined();
    expect(qc.getQueryData(["skill", "skill-b", undefined])).toBeDefined();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns SkillResponse on success", async () => {
    const response = makeSkillResponse({
      skill: "leadership-advisor",
      model_used: "cerebras-qwen",
      output: { tip: "Lead with empathy" },
    });
    mockApiFetch.mockResolvedValue(response);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () => useSkill("leadership-advisor"),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.skill).toBe("leadership-advisor");
    expect(result.current.data?.model_used).toBe("cerebras-qwen");
    expect(result.current.data?.output).toEqual({ tip: "Lead with empathy" });
  });
});
