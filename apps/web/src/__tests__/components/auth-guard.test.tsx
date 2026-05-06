import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";

const mockRouterReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockRouterReplace }),
  useParams: () => ({ locale: "az" }),
}));

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: mockOnAuthStateChange,
    },
  }),
}));

const authStore = vi.hoisted(() => {
  const mockAuthStore = {
    session: null as null | { user: { id: string }; access_token: string },
    isLoading: true,
    setSession: vi.fn(),
    setLoading: vi.fn(),
  };

  return {
    mockAuthStore,
    useAuthStore: Object.assign(() => mockAuthStore, {
      getState: () => mockAuthStore,
    }),
  };
});

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: authStore.useAuthStore,
}));

import { AuthGuard } from "@/components/layout/auth-guard";

function fakeSession() {
  return { user: { id: "user-1" }, access_token: "tok" };
}

function makeSubscription() {
  return { data: { subscription: { unsubscribe: vi.fn() } } };
}

describe("AuthGuard — loading state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStore.mockAuthStore.isLoading = true;
    authStore.mockAuthStore.session = null;
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockOnAuthStateChange.mockReturnValue(makeSubscription());
  });

  it("renders loading spinner while isLoading is true", () => {
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("loading container has accessible aria-label", () => {
    render(
      <AuthGuard>
        <div>Protected</div>
      </AuthGuard>,
    );
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("does not render children while loading", () => {
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });
});

describe("AuthGuard — unauthenticated redirect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStore.mockAuthStore.isLoading = false;
    authStore.mockAuthStore.session = null;
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockOnAuthStateChange.mockReturnValue(makeSubscription());
  });

  it("redirects to login when session is null after load", async () => {
    render(
      <AuthGuard>
        <div>Protected</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(mockRouterReplace).toHaveBeenCalledWith("/az/login");
    });
  });

  it("renders null (no children, no spinner) when not loading and no session", () => {
    const { container } = render(
      <AuthGuard>
        <div>Protected</div>
      </AuthGuard>,
    );
    expect(container).toBeEmptyDOMElement();
  });
});

describe("AuthGuard — authenticated user", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStore.mockAuthStore.isLoading = false;
    authStore.mockAuthStore.session = fakeSession();
    mockGetSession.mockResolvedValue({ data: { session: fakeSession() } });
    mockOnAuthStateChange.mockReturnValue(makeSubscription());
  });

  it("renders children when session exists and not loading", () => {
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("does not redirect when session is present", async () => {
    render(
      <AuthGuard>
        <div>Protected</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(authStore.mockAuthStore.setSession).toHaveBeenCalled();
    });
    expect(mockRouterReplace).not.toHaveBeenCalled();
  });
});

describe("AuthGuard — getSession effect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStore.mockAuthStore.isLoading = true;
    authStore.mockAuthStore.session = null;
    mockOnAuthStateChange.mockReturnValue(makeSubscription());
  });

  it("calls setSession with null when getSession returns no session", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(authStore.mockAuthStore.setSession).toHaveBeenCalledWith(null);
    });
  });

  it("calls setLoading(false) after getSession resolves", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(authStore.mockAuthStore.setLoading).toHaveBeenCalledWith(false);
    });
  });

  it("calls setSession with session object when authenticated", async () => {
    const session = fakeSession();
    mockGetSession.mockResolvedValue({ data: { session } });
    render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(authStore.mockAuthStore.setSession).toHaveBeenCalledWith(session);
    });
  });
});

describe("AuthGuard — onAuthStateChange subscription", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStore.mockAuthStore.isLoading = false;
    authStore.mockAuthStore.session = fakeSession();
    mockGetSession.mockResolvedValue({ data: { session: fakeSession() } });
  });

  it("subscribes to auth state changes on mount", () => {
    const unsubscribe = vi.fn();
    mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe } } });
    render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
    );
    expect(mockOnAuthStateChange).toHaveBeenCalled();
  });

  it("unsubscribes on unmount", () => {
    const unsubscribe = vi.fn();
    mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe } } });
    const { unmount } = render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
    );
    unmount();
    expect(unsubscribe).toHaveBeenCalled();
  });

  it("redirects to login when auth state changes to null session", () => {
    let capturedCallback: (event: string, session: null) => void = () => {};
    mockOnAuthStateChange.mockImplementation((cb) => {
      capturedCallback = cb;
      return makeSubscription();
    });
    render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
    );
    capturedCallback("SIGNED_OUT", null);
    expect(mockRouterReplace).toHaveBeenCalledWith("/az/login");
  });
});
