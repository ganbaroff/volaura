import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { mockRouter, mockSupabaseAuth } from "@/test/mocks.js";
import LoginPage from "./page";

// Need to mock Suspense for tests
vi.mock("react", async () => {
  const actual = await vi.importActual<typeof import("react")>("react");
  return {
    ...actual,
    Suspense: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders login form with email and password fields", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText("auth.email")).toBeInTheDocument();
    expect(screen.getByLabelText("auth.password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "auth.loginAction" })).toBeInTheDocument();
  });

  it("renders signup link", () => {
    render(<LoginPage />);
    expect(screen.getByText("auth.signup")).toBeInTheDocument();
  });

  it("shows loading state during submission", async () => {
    // Make signIn hang
    mockSupabaseAuth.signInWithPassword.mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "test@volaura.com" },
    });
    fireEvent.change(screen.getByLabelText("auth.password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.loginAction" }));

    await waitFor(() => {
      expect(screen.getByRole("button")).toHaveTextContent("auth.loggingIn");
      expect(screen.getByRole("button")).toBeDisabled();
    });
  });

  it("shows error message on auth failure", async () => {
    mockSupabaseAuth.signInWithPassword.mockResolvedValue({
      data: { session: null },
      error: { message: "Invalid login credentials" },
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "test@volaura.com" },
    });
    fireEvent.change(screen.getByLabelText("auth.password"), {
      target: { value: "wrong" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.loginAction" }));

    await waitFor(() => {
      expect(screen.getByText("Invalid login credentials")).toBeInTheDocument();
    });
  });

  it("redirects to dashboard on successful login", async () => {
    mockSupabaseAuth.signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "abc", user: { id: "1" } } },
      error: null,
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "test@volaura.com" },
    });
    fireEvent.change(screen.getByLabelText("auth.password"), {
      target: { value: "correct" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.loginAction" }));

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/en/dashboard");
    });
  });

  it("prevents open redirect with protocol-relative URL", async () => {
    // Simulate ?next=//evil.com — should redirect to dashboard, not evil.com
    const originalGet = URLSearchParams.prototype.get;
    vi.spyOn(URLSearchParams.prototype, "get").mockImplementation(function (this: URLSearchParams, key: string) {
      if (key === "next") return "//evil.com";
      return originalGet.call(this, key);
    });

    mockSupabaseAuth.signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "abc", user: { id: "1" } } },
      error: null,
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "test@volaura.com" },
    });
    fireEvent.change(screen.getByLabelText("auth.password"), {
      target: { value: "correct" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.loginAction" }));

    await waitFor(() => {
      // Should redirect to dashboard, NOT //evil.com
      expect(mockRouter.push).toHaveBeenCalledWith("/en/dashboard");
      expect(mockRouter.push).not.toHaveBeenCalledWith("//evil.com");
    });

    vi.restoreAllMocks();
  });
});
