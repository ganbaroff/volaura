import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Mocks (declared before module import) ──────────────────────────────────────

const mockGetUser = vi.fn();
const mockRedirect = vi.fn();

vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(() => ({
    auth: { getUser: mockGetUser },
  })),
}));

vi.mock("next/server", async () => {
  const actual = await vi.importActual<typeof import("next/server")>("next/server");
  return {
    ...actual,
    NextResponse: {
      ...actual.NextResponse,
      redirect: (url: URL) => {
        mockRedirect(url);
        return { redirected: true, redirectUrl: url, cookies: { set: vi.fn() } };
      },
    },
  };
});

// ── Import after mocks ────────────────────────────────────────────────────────

import { updateSession } from "@/lib/supabase/middleware";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeRequest(pathname: string) {
  const url = `https://volaura.app${pathname}`;
  return {
    nextUrl: {
      pathname,
      clone: () => new URL(url),
    },
    cookies: {
      getAll: vi.fn().mockReturnValue([]),
      set: vi.fn(),
    },
  } as unknown as import("next/server").NextRequest;
}

function makeResponse() {
  return {
    cookies: { set: vi.fn() },
    _sentinel: "base-response",
  } as unknown as import("next/server").NextResponse;
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("updateSession — env var guard", () => {
  const originalUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const originalKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  afterEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = originalUrl;
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = originalKey;
    vi.clearAllMocks();
  });

  it("returns the original response unchanged when URL is missing", async () => {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";

    const req = makeRequest("/az/dashboard");
    const res = makeResponse();

    const result = await updateSession(req, res);
    expect(result).toBe(res);
    expect(mockGetUser).not.toHaveBeenCalled();
  });

  it("returns the original response unchanged when anon key is missing", async () => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://proj.supabase.co";
    delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    const req = makeRequest("/az/dashboard");
    const res = makeResponse();

    const result = await updateSession(req, res);
    expect(result).toBe(res);
    expect(mockGetUser).not.toHaveBeenCalled();
  });

  it("returns the original response unchanged when both env vars missing", async () => {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    const req = makeRequest("/az/profile");
    const res = makeResponse();

    const result = await updateSession(req, res);
    expect(result).toBe(res);
  });
});

describe("updateSession — callback route skip", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://proj.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";
    vi.clearAllMocks();
  });

  it("skips auth check and returns response on /callback route", async () => {
    const req = makeRequest("/az/callback");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockGetUser).not.toHaveBeenCalled();
  });

  it("skips auth on /auth/callback path", async () => {
    const req = makeRequest("/en/auth/callback");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockGetUser).not.toHaveBeenCalled();
  });

  it("skips auth on callback with query params", async () => {
    const req = makeRequest("/az/callback?code=abc123");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockGetUser).not.toHaveBeenCalled();
  });
});

describe("updateSession — authenticated user on protected routes", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://proj.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";
    vi.clearAllMocks();
    mockGetUser.mockResolvedValue({ data: { user: { id: "user-123" } } });
  });

  it("returns original response for authenticated user on /dashboard", async () => {
    const req = makeRequest("/az/dashboard");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });

  it("returns original response for authenticated user on /aura", async () => {
    const req = makeRequest("/en/aura");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });

  it("returns original response for authenticated user on /profile", async () => {
    const req = makeRequest("/az/profile");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });

  it("returns original response for authenticated user on /settings", async () => {
    const req = makeRequest("/en/settings");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });
});

describe("updateSession — unauthenticated user redirect", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://proj.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";
    vi.clearAllMocks();
    mockGetUser.mockResolvedValue({ data: { user: null } });
  });

  it("redirects to login on /dashboard when unauthenticated", async () => {
    const req = makeRequest("/az/dashboard");
    const res = makeResponse();

    await updateSession(req, res);

    expect(mockRedirect).toHaveBeenCalled();
    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/az/login");
  });

  it("redirects to login on /aura when unauthenticated", async () => {
    const req = makeRequest("/en/aura");
    const res = makeResponse();

    await updateSession(req, res);

    expect(mockRedirect).toHaveBeenCalled();
    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/en/login");
  });

  it("redirects to login on /profile when unauthenticated", async () => {
    const req = makeRequest("/az/profile");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/az/login");
  });

  it("redirects to login on /settings when unauthenticated", async () => {
    const req = makeRequest("/en/settings");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/en/login");
  });

  it("sets next search param to original pathname on redirect", async () => {
    const req = makeRequest("/az/dashboard");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.searchParams.get("next")).toBe("/az/dashboard");
  });

  it("preserves next param for /aura path", async () => {
    const req = makeRequest("/en/aura");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.searchParams.get("next")).toBe("/en/aura");
  });
});

describe("updateSession — locale extraction from path", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://proj.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";
    vi.clearAllMocks();
    mockGetUser.mockResolvedValue({ data: { user: null } });
  });

  it("extracts 'az' locale from /az/dashboard", async () => {
    const req = makeRequest("/az/dashboard");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/az/login");
  });

  it("extracts 'en' locale from /en/dashboard", async () => {
    const req = makeRequest("/en/dashboard");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/en/login");
  });

  it("falls back to 'az' for unknown locale prefix", async () => {
    const req = makeRequest("/fr/dashboard");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/az/login");
  });

  it("falls back to 'az' for path with no locale prefix", async () => {
    const req = makeRequest("/dashboard");
    const res = makeResponse();

    await updateSession(req, res);

    const redirectUrl: URL = mockRedirect.mock.calls[0][0];
    expect(redirectUrl.pathname).toBe("/az/login");
  });
});

describe("updateSession — non-protected routes", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://proj.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon-key";
    vi.clearAllMocks();
    mockGetUser.mockResolvedValue({ data: { user: null } });
  });

  it("does not redirect unauthenticated user on public home page", async () => {
    const req = makeRequest("/az");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });

  it("does not redirect unauthenticated user on /login", async () => {
    const req = makeRequest("/az/login");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });

  it("does not redirect unauthenticated user on /register", async () => {
    const req = makeRequest("/en/register");
    const res = makeResponse();

    const result = await updateSession(req, res);

    expect(result).toBe(res);
    expect(mockRedirect).not.toHaveBeenCalled();
  });
});
