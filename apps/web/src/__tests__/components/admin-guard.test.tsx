import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockRouterReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockRouterReplace }),
  useParams: () => ({ locale: "az" }),
}));

// Mock Skeleton so it renders a simple div (avoids CSS issues in jsdom)
vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) =>
    React.createElement("div", { "data-testid": "skeleton", className }),
}));

const mockAuthStore = {
  session: null as null | object,
  isLoading: false,
};

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: () => mockAuthStore,
}));

const mockAdminPing = {
  data: undefined as boolean | undefined,
  isLoading: false,
};

vi.mock("@/hooks/queries/use-admin", () => ({
  useAdminPing: () => mockAdminPing,
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { AdminGuard } from "@/components/layout/admin-guard";

// ── Helpers ───────────────────────────────────────────────────────────────────

function fakeSession() {
  return { user: { id: "admin-1" }, access_token: "tok" };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("AdminGuard — loading state", () => {
  it("shows skeleton loading UI when sessionLoading is true", () => {
    mockAuthStore.session = null;
    mockAuthStore.isLoading = true;
    mockAdminPing.data = undefined;
    mockAdminPing.isLoading = false;

    render(
      <AdminGuard>
        <div>Admin content</div>
      </AdminGuard>
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("shows skeleton loading UI when pingLoading is true", () => {
    mockAuthStore.session = fakeSession();
    mockAuthStore.isLoading = false;
    mockAdminPing.data = undefined;
    mockAdminPing.isLoading = true;

    render(
      <AdminGuard>
        <div>Admin content</div>
      </AdminGuard>
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("does not render children while either loading flag is true", () => {
    mockAuthStore.session = fakeSession();
    mockAuthStore.isLoading = true;
    mockAdminPing.data = true;
    mockAdminPing.isLoading = false;

    render(
      <AdminGuard>
        <div>Admin content</div>
      </AdminGuard>
    );
    expect(screen.queryByText("Admin content")).not.toBeInTheDocument();
  });

  it("renders skeleton cards (6) during loading", () => {
    mockAuthStore.session = null;
    mockAuthStore.isLoading = true;
    mockAdminPing.data = undefined;
    mockAdminPing.isLoading = false;

    render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    // 1 header skeleton + 6 grid skeletons = 7
    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThanOrEqual(6);
  });
});

describe("AdminGuard — no session redirect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthStore.isLoading = false;
    mockAdminPing.isLoading = false;
  });

  it("redirects to login when session is null", () => {
    mockAuthStore.session = null;
    mockAdminPing.data = undefined;

    render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    expect(mockRouterReplace).toHaveBeenCalledWith("/az/login");
  });

  it("renders null when session is null and not loading", () => {
    mockAuthStore.session = null;
    mockAdminPing.data = undefined;

    const { container } = render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    expect(container).toBeEmptyDOMElement();
  });
});

describe("AdminGuard — non-admin redirect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthStore.isLoading = false;
    mockAdminPing.isLoading = false;
  });

  it("redirects to dashboard when session exists but isAdmin is false", () => {
    mockAuthStore.session = fakeSession();
    mockAdminPing.data = false;

    render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    expect(mockRouterReplace).toHaveBeenCalledWith("/az/dashboard");
  });

  it("does not redirect to login for authenticated non-admin", () => {
    mockAuthStore.session = fakeSession();
    mockAdminPing.data = false;

    render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    expect(mockRouterReplace).not.toHaveBeenCalledWith("/az/login");
  });

  it("renders null for authenticated non-admin", () => {
    mockAuthStore.session = fakeSession();
    mockAdminPing.data = false;

    const { container } = render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    expect(container).toBeEmptyDOMElement();
  });
});

describe("AdminGuard — admin user passes through", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthStore.isLoading = false;
    mockAdminPing.isLoading = false;
  });

  it("renders children when session exists and isAdmin is true", () => {
    mockAuthStore.session = fakeSession();
    mockAdminPing.data = true;

    render(
      <AdminGuard>
        <div>Admin content</div>
      </AdminGuard>
    );
    expect(screen.getByText("Admin content")).toBeInTheDocument();
  });

  it("does not redirect when both session and admin check pass", () => {
    mockAuthStore.session = fakeSession();
    mockAdminPing.data = true;

    render(
      <AdminGuard>
        <div>Admin content</div>
      </AdminGuard>
    );
    expect(mockRouterReplace).not.toHaveBeenCalled();
  });
});

describe("AdminGuard — pending ping (undefined)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthStore.isLoading = false;
    mockAdminPing.isLoading = false;
  });

  it("renders null when session exists but isAdmin is undefined (ping not resolved)", () => {
    mockAuthStore.session = fakeSession();
    mockAdminPing.data = undefined;

    const { container } = render(
      <AdminGuard>
        <div>Admin</div>
      </AdminGuard>
    );
    // !session || !isAdmin — undefined is falsy, so guard blocks
    expect(container).toBeEmptyDOMElement();
  });
});
