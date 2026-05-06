import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";

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

const authStore = vi.hoisted(() => {
  const mockSetSession = vi.fn();
  const mockSetLoading = vi.fn();

  type MockSession = null | { user: { id: string }; access_token: string };
  type MockStoreState = {
    session: MockSession;
    isLoading: boolean;
    setSession: typeof mockSetSession;
    setLoading: typeof mockSetLoading;
  };

  let storeState: MockStoreState = {
    session: null,
    isLoading: true,
    setSession: mockSetSession,
    setLoading: mockSetLoading,
  };

  return {
    mockSetSession,
    mockSetLoading,
    useAuthStore: Object.assign(() => storeState, {
      getState: () => storeState,
    }),
    setStoreState: (next: MockStoreState) => {
      storeState = next;
    },
    getStoreState: () => storeState,
  };
});

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: authStore.useAuthStore,
}));

import { AuthGuard } from "./auth-guard";

function fakeSession() {
  return { user: { id: "user-1" }, access_token: "tok" };
}

function makeSubscription() {
  return { data: { subscription: { unsubscribe: mockUnsubscribe } } };
}

describe("AuthGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStore.setStoreState({
      session: null,
      isLoading: true,
      setSession: authStore.mockSetSession,
      setLoading: authStore.mockSetLoading,
    });
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockOnAuthStateChange.mockReturnValue(makeSubscription());
  });

  it("shows spinner with role=status and aria-label=Loading while isLoading is true", () => {
    render(<AuthGuard><div>Child</div></AuthGuard>);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("does not render children while loading", () => {
    render(<AuthGuard><div>Protected</div></AuthGuard>);
    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  it("renders nothing when not loading and session is null", () => {
    authStore.setStoreState({ ...authStore.getStoreState(), isLoading: false, session: null });
    const { container } = render(<AuthGuard><div>Protected</div></AuthGuard>);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders children when session exists and not loading", () => {
    authStore.setStoreState({ ...authStore.getStoreState(), isLoading: false, session: fakeSession() });
    render(<AuthGuard><div>Protected</div></AuthGuard>);
    expect(screen.getByText("Protected")).toBeInTheDocument();
  });

  it("redirects to login when getSession returns null session", async () => {
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/az/login");
    });
  });

  it("calls setSession with session when getSession returns a session", async () => {
    const session = fakeSession();
    mockGetSession.mockResolvedValue({ data: { session } });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(authStore.mockSetSession).toHaveBeenCalledWith(session);
    });
  });

  it("calls setLoading(false) after getSession resolves", async () => {
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(authStore.mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

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
    authStore.setStoreState({ ...authStore.getStoreState(), isLoading: false, session: fakeSession() });
    let capturedCb: (event: string, session: null) => void = () => {};
    mockOnAuthStateChange.mockImplementation((cb: typeof capturedCb) => {
      capturedCb = cb;
      return makeSubscription();
    });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    capturedCb("INITIAL_SESSION", null);
    expect(mockReplace).not.toHaveBeenCalled();
    expect(authStore.mockSetSession).not.toHaveBeenCalledWith(null);
  });

  it("calls setSession when onAuthStateChange emits a valid session", () => {
    const session = fakeSession();
    let capturedCb: (event: string, sess: typeof session | null) => void = () => {};
    mockOnAuthStateChange.mockImplementation((cb: typeof capturedCb) => {
      capturedCb = cb;
      return makeSubscription();
    });
    render(<AuthGuard><div>Child</div></AuthGuard>);
    capturedCb("SIGNED_IN", session);
    expect(authStore.mockSetSession).toHaveBeenCalledWith(session);
  });

  it("calls unsubscribe on unmount", () => {
    const unsubscribe = vi.fn();
    mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe } } });
    const { unmount } = render(<AuthGuard><div>Child</div></AuthGuard>);
    unmount();
    expect(unsubscribe).toHaveBeenCalled();
  });

  it("uses locale from useParams in the redirect path", async () => {
    render(<AuthGuard><div>Child</div></AuthGuard>);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(expect.stringMatching(/^\/az\/login$/));
    });
  });
});
