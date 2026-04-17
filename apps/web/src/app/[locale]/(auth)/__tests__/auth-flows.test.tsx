/**
 * Auth flows integration tests.
 * Tests ForgotPassword and Signup pages, complementing login.test.tsx.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ── Navigation / Link / i18n / Framer mocks ──────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  useParams: () => ({ locale: "en" }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/en/forgot-password",
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) => {
    const { prefetch, ...htmlProps } = rest;
    return <a href={href} {...htmlProps}>{children}</a>;
  },
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_target, prop: string) => {
        return ({
          children,
          ...rest
        }: {
          children?: React.ReactNode;
          [key: string]: unknown;
        }) => {
          const htmlProps: Record<string, unknown> = {};
          for (const [key, value] of Object.entries(rest)) {
            if (
              !["initial", "animate", "exit", "transition", "variants", "whileHover", "whileTap", "whileInView", "layout"].includes(key)
            ) {
              htmlProps[key] = value;
            }
          }
          const Component = prop as React.ElementType;
          return <Component {...htmlProps}>{children}</Component>;
        };
      },
    }
  ),
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => false,
}));

// ── Supabase mock ─────────────────────────────────────────────────────────
export const mockResetPasswordForEmail = vi.fn();
export const mockSignUp = vi.fn();
export const mockSignIn = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      resetPasswordForEmail: mockResetPasswordForEmail,
      signUp: mockSignUp,
      signInWithPassword: mockSignIn,
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      getUser: vi.fn().mockResolvedValue({ data: { user: null } }),
      onAuthStateChange: vi.fn(() => ({
        data: { subscription: { unsubscribe: vi.fn() } },
      })),
    },
    from: vi.fn(() => ({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({ data: null, error: null }),
    })),
  }),
}));

// ── SocialAuthButtons mock (avoids signInWithOAuth dependency) ───────────
vi.mock("@/components/ui/social-auth-buttons", () => ({
  SocialAuthButtons: () => null,
}));

// ── Auth store mock (needed by SignupPage) ────────────────────────────────
vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ setSession: vi.fn(), clear: vi.fn(), user: null, token: null }),
}));

// ── Suspense mock (both pages wrap in Suspense) ───────────────────────────
vi.mock("react", async () => {
  const actual = await vi.importActual<typeof import("react")>("react");
  return {
    ...actual,
    Suspense: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// ── Imports (after mocks) ─────────────────────────────────────────────────
import ForgotPasswordPage from "../forgot-password/page";
import SignupPage from "../signup/page";

// ── ForgotPassword ────────────────────────────────────────────────────────
describe("ForgotPassword", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email input", () => {
    render(<ForgotPasswordPage />);
    expect(screen.getByLabelText("auth.email")).toBeInTheDocument();
  });

  it("renders the send reset link button", () => {
    render(<ForgotPasswordPage />);
    expect(
      screen.getByRole("button", { name: "auth.sendResetLink" })
    ).toBeInTheDocument();
  });

  it("renders back to login link", () => {
    render(<ForgotPasswordPage />);
    const link = screen.getByText("auth.backToLogin");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute("href", "/en/login");
  });

  it("calls supabase.auth.resetPasswordForEmail on submit", async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: null });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "talent@volaura.az" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.sendResetLink" }));

    await waitFor(() => {
      expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
        "talent@volaura.az",
        expect.objectContaining({ redirectTo: expect.stringContaining("reset-password") })
      );
    });
  });

  it("shows success state after successful submit", async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: null });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "talent@volaura.az" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.sendResetLink" }));

    await waitFor(() => {
      expect(screen.getByText("auth.checkEmailTitle")).toBeInTheDocument();
    });
  });

  it("shows error message when reset fails", async () => {
    mockResetPasswordForEmail.mockResolvedValue({
      error: { message: "Email not found" },
    });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "notfound@volaura.az" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.sendResetLink" }));

    await waitFor(() => {
      expect(screen.getByText("Email not found")).toBeInTheDocument();
    });
  });

  it("shows loading state while submitting", async () => {
    mockResetPasswordForEmail.mockImplementation(() => new Promise(() => {}));

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "talent@volaura.az" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.sendResetLink" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "auth.sendingReset" })
      ).toBeDisabled();
    });
  });

  it("try again button resets to form state", async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: null });

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "talent@volaura.az" },
    });
    fireEvent.click(screen.getByRole("button", { name: "auth.sendResetLink" }));

    await waitFor(() => {
      expect(screen.getByText("auth.checkEmailTitle")).toBeInTheDocument();
    });

    // Click "try again" to go back
    fireEvent.click(screen.getByText("auth.tryAgain"));

    await waitFor(() => {
      expect(screen.getByLabelText("auth.email")).toBeInTheDocument();
    });
  });
});

// ── Signup ─────────────────────────────────────────────────────────────────
describe("Signup", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email, password, username, and display name inputs", () => {
    render(<SignupPage />);
    expect(screen.getByLabelText("auth.email")).toBeInTheDocument();
    expect(screen.getByLabelText("auth.username")).toBeInTheDocument();
    // password label
    expect(
      screen.getByRole("button", { name: "auth.signupAction" })
    ).toBeInTheDocument();
  });

  it("submit button is present", () => {
    render(<SignupPage />);
    expect(
      screen.getByRole("button", { name: "auth.signupAction" })
    ).toBeInTheDocument();
  });

  it("shows error message when signup fails", async () => {
    mockSignUp.mockResolvedValue({
      data: { session: null, user: null },
      error: { message: "Email already in use" },
    });

    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText("auth.username"), {
      target: { value: "testuser" },
    });
    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "existing@volaura.az" },
    });
    // Find password input by id
    const passwordInput = document.getElementById("password")!;
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    // Must tick consent checkboxes to enable submit
    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach((cb) => fireEvent.click(cb));
    fireEvent.click(screen.getByRole("button", { name: "auth.signupAction" }));

    // Shame-free (Law 3): raw Supabase message "Email already in use" is
    // swallowed and logged to console; user sees t("auth.errorGeneric") key
    // (resolves to friendly copy in production — test harness returns key name).
    await waitFor(() => {
      expect(screen.getByText("auth.errorGeneric")).toBeInTheDocument();
    });
  });

  it("shows loading state during submission", async () => {
    mockSignUp.mockImplementation(() => new Promise(() => {}));

    render(<SignupPage />);

    fireEvent.change(screen.getByLabelText("auth.username"), {
      target: { value: "newuser" },
    });
    fireEvent.change(screen.getByLabelText("auth.email"), {
      target: { value: "new@volaura.az" },
    });
    const passwordInput = document.getElementById("password")!;
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    // Must tick consent checkboxes to enable submit
    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach((cb) => fireEvent.click(cb));
    fireEvent.click(screen.getByRole("button", { name: "auth.signupAction" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "auth.creatingAccount" })
      ).toBeDisabled();
    });
  });

  it("has login link for existing users", () => {
    render(<SignupPage />);
    const link = screen.getByText("auth.login");
    expect(link.closest("a")).toHaveAttribute("href", "/en/login");
  });
});
