import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
  useParams: () => ({ locale: "az" }),
}));

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockUnsubscribe = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: mockOnAuthStateChange,
    },
  }),
}));

const mockSetSession = vi.fn();
const mockSetLoading = vi.fn();

let storeState: {
  session: null | { user: { id: string }; access_token: string };
  isLoading: boolean;
  setSession: typeof mockSetSession;
  setLoading: typeof mockSetLoading;
} = {
  session: null,
  isLoading: true,
  setSession: mockSetSession,
  setLoading: mockSetLoading,
};

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: () => storeState,
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { AuthGuard } from "./auth-guard";

// ── Helpers ───────────────────────────────────────────────────────────────────

function fakeSession() {
  return { user: { id: "user-1" }, access_token: "tok" };
}

function makeSubscription() {
  return { data: { subscription: { unsubscribe: mockUnsubscribe } } };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("AuthGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    storeState = {
      session: null,
      isLoading: true,
      setSession: mockSetSession,
      setLoading: mockSetLoading,
    };
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockOnAuthStateChange.mockReturnValue(makeSubscription());
  });

  // 1. Loading state
  it("shows spinner with role=status and aria-label=Loading while isLoading is true", () => {
    render(<AuthGuard><div>Child</div></AuthGuard>);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("does not render children while loading", () => {
    render(<AuthGuard><div>Protected</div></AuthGuard>);
    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  // 2. No session + not loading — renders null
  it("renders nothing when not loading and session is null", () => {
    storeState = { ...storeState, isLoading: false, session: null };
    const { container } = render(<AuthGuard><div>Protected</div></AuthGuard>);
    expect(container).toBeEmptyDOMElement();
  });

  // 3. Authenticated — renders children
  it("renders children when session exists and not loading", () => {
    storeState = { ...storeState, isLoading: false, session: fakeSession() };
    render(<AuthGuard><div>Protected</div></AuthGuard>);
    expect(screen.getByText("Protected")).toBeInTheDocument();
  });

  // 4. getSession returns null — redirects to login
  it("redirects to login when getSession returns null session", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/az/login");
    });
  });

  // 5. getSession returns valid session — calls setSession
  it("calls setSession with session when getSession returns a session", async () => {
    const session = fakeSession();
    mockGetSession.mockResolvedValue({ data: { session } });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(mockSetSession).toHaveBeenCalledWith(session);
    });
  });

  it("calls setLoading(false) after getSession resolves", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  // 6. onAuthStateChange fires with null — redirects to login
  it("redirects to login when onAuthStateChange emits null session", () => {
    let capturedCb: (event: string, session: null) => void = () => {};
    mockOnAuthStateChange.mockImplementation((cb: typeof capturedCb) => {
      capturedCb = cb;
      return makeSubscription();
    });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    capturedCb("SIGNED_OUT", null);
    expect(mockReplace).toHaveBeenCalledWith("/az/login");
  });

  it("does not redirect on transient INITIAL_SESSION null when a cached session exists", () => {
    storeState = { ...storeState, isLoading: false, session: fakeSession() };
    let capturedCb: (event: string, session: null) => void = () => {};
    mockOnAuthStateChange.mockImplementation((cb: typeof capturedCb) => {
      capturedCb = cb;
      return makeSubscription();
    });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    capturedCb("INITIAL_SESSION", null);
    expect(mockReplace).not.toHaveBeenCalled();
    expect(mockSetSession).not.toHaveBeenCalledWith(null);
  });

  // 7. onAuthStateChange fires with session — calls setSession
  it("calls setSession when onAuthStateChange emits a valid session", () => {
    const session = fakeSession();
    let capturedCb: (event: string, sess: typeof session | null) => void = () => {};
    mockOnAuthStateChange.mockImplementation((cb: typeof capturedCb) => {
      capturedCb = cb;
      return makeSubscription();
    });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    capturedCb("SIGNED_IN", session);
    expect(mockSetSession).toHaveBeenCalledWith(session);
  });

  // 8. Cleanup unsubscribes on unmount
  it("calls unsubscribe on unmount", () => {
    const unsubscribe = vi.fn();
    mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe } } });
    const { unmount } = render(<AuthGuard><div>Child</div></AuthGuard>);
    unmount();
    expect(unsubscribe).toHaveBeenCalled();
  });

  // 9. Uses correct locale in redirect path
  it("uses locale from useParams in the redirect path", async () => {
    // useParams is mocked to return { locale: "az" } — redirect must be /az/login
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(expect.stringMatching(/^\/az\/login$/));
    });
  });
});
