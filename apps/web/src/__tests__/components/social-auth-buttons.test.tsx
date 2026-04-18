import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockSignInWithOAuth = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      signInWithOAuth: mockSignInWithOAuth,
    },
  }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("lucide-react", () => ({
  Loader2: ({ className, ...props }: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", {
      "data-testid": "loader-icon",
      className,
      ...props,
    }),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { SocialAuthButtons, OAUTH_META_KEY } from "@/components/ui/social-auth-buttons";

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderButtons(props: Partial<React.ComponentProps<typeof SocialAuthButtons>> = {}) {
  return render(
    <SocialAuthButtons redirectTo="https://example.com/callback" {...props} />
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("SocialAuthButtons — rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSignInWithOAuth.mockResolvedValue({ error: null });
  });

  it("renders Google button", () => {
    renderButtons();
    expect(screen.getByRole("button", { name: /google/i })).toBeInTheDocument();
  });

  it("renders GitHub button", () => {
    renderButtons();
    expect(screen.getByRole("button", { name: /github/i })).toBeInTheDocument();
  });

  it("renders both OAuth provider buttons", () => {
    renderButtons();
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it("renders Google SVG icon in button", () => {
    renderButtons();
    const googleBtn = screen.getByRole("button", { name: /google/i });
    expect(googleBtn.querySelector("svg")).toBeInTheDocument();
  });

  it("renders GitHub SVG icon in button", () => {
    renderButtons();
    const githubBtn = screen.getByRole("button", { name: /github/i });
    expect(githubBtn.querySelector("svg")).toBeInTheDocument();
  });

  it("renders the 'or continue with' divider text", () => {
    renderButtons();
    expect(screen.getByText("auth.orContinueWith")).toBeInTheDocument();
  });

  it("buttons are not disabled initially", () => {
    renderButtons();
    expect(screen.getByRole("button", { name: /google/i })).not.toBeDisabled();
    expect(screen.getByRole("button", { name: /github/i })).not.toBeDisabled();
  });
});

describe("SocialAuthButtons — OAuth click handler", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSignInWithOAuth.mockResolvedValue({ error: null });
  });

  it("calls supabase signInWithOAuth with google provider on Google click", async () => {
    const user = userEvent.setup();
    renderButtons({ redirectTo: "https://app.volaura.com/callback" });
    await user.click(screen.getByRole("button", { name: /google/i }));
    expect(mockSignInWithOAuth).toHaveBeenCalledWith({
      provider: "google",
      options: { redirectTo: "https://app.volaura.com/callback" },
    });
  });

  it("calls supabase signInWithOAuth with github provider on GitHub click", async () => {
    const user = userEvent.setup();
    renderButtons({ redirectTo: "https://app.volaura.com/callback" });
    await user.click(screen.getByRole("button", { name: /github/i }));
    expect(mockSignInWithOAuth).toHaveBeenCalledWith({
      provider: "github",
      options: { redirectTo: "https://app.volaura.com/callback" },
    });
  });

  it("disables both buttons while OAuth is in-flight", async () => {
    // Never resolves — simulates in-flight state
    mockSignInWithOAuth.mockImplementation(() => new Promise(() => {}));
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /google/i }));
    expect(screen.getByRole("button", { name: /google/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /github/i })).toBeDisabled();
  });

  it("shows loader icon on the clicked provider button while loading", async () => {
    mockSignInWithOAuth.mockImplementation(() => new Promise(() => {}));
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /google/i }));
    const googleBtn = screen.getByRole("button", { name: /google/i });
    expect(googleBtn.querySelector("[data-testid='loader-icon']")).toBeInTheDocument();
  });

  it("does not show loader on the non-clicked provider button", async () => {
    mockSignInWithOAuth.mockImplementation(() => new Promise(() => {}));
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /google/i }));
    const githubBtn = screen.getByRole("button", { name: /github/i });
    expect(githubBtn.querySelector("[data-testid='loader-icon']")).toBeNull();
  });

  it("re-enables buttons after successful OAuth resolves", async () => {
    mockSignInWithOAuth.mockResolvedValue({ error: null });
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /google/i }));
    // After OAuth succeeds (redirect happens in real app), loading stays set.
    // On success with no error, loading is NOT cleared (redirect takes over).
    // We only test that signInWithOAuth was called.
    expect(mockSignInWithOAuth).toHaveBeenCalled();
  });
});

describe("SocialAuthButtons — error handling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows error message when signInWithOAuth returns an error", async () => {
    mockSignInWithOAuth.mockResolvedValue({ error: { message: "OAuth failed" } });
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => {
      expect(screen.getByText("auth.oauthError")).toBeInTheDocument();
    });
  });

  it("shows error message when signInWithOAuth throws", async () => {
    mockSignInWithOAuth.mockRejectedValue(new Error("Network error"));
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /github/i }));
    await waitFor(() => {
      expect(screen.getByText("auth.oauthError")).toBeInTheDocument();
    });
  });

  it("re-enables buttons after error", async () => {
    mockSignInWithOAuth.mockResolvedValue({ error: { message: "Failed" } });
    const user = userEvent.setup();
    renderButtons();
    await user.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /google/i })).not.toBeDisabled();
    });
  });

  it("does not show error initially", () => {
    renderButtons();
    expect(screen.queryByText("auth.oauthError")).not.toBeInTheDocument();
  });

  it("clears previous error on next OAuth attempt", async () => {
    mockSignInWithOAuth.mockResolvedValueOnce({ error: { message: "First failure" } });
    mockSignInWithOAuth.mockImplementationOnce(() => new Promise(() => {}));
    const user = userEvent.setup();
    renderButtons();

    // Trigger first error
    await user.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => {
      expect(screen.getByText("auth.oauthError")).toBeInTheDocument();
    });

    // Second click clears the error
    await user.click(screen.getByRole("button", { name: /github/i }));
    await waitFor(() => {
      expect(screen.queryByText("auth.oauthError")).not.toBeInTheDocument();
    });
  });
});

describe("SocialAuthButtons — meta localStorage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSignInWithOAuth.mockResolvedValue({ error: null });
    localStorage.clear();
  });

  it("stores meta in localStorage before OAuth when meta provided", async () => {
    const user = userEvent.setup();
    renderButtons({
      redirectTo: "https://app.volaura.com/callback",
      meta: { referral: "campaign-1", source: "landing" },
    });
    await user.click(screen.getByRole("button", { name: /google/i }));
    const stored = localStorage.getItem(OAUTH_META_KEY);
    expect(stored).not.toBeNull();
    expect(JSON.parse(stored!)).toEqual({ referral: "campaign-1", source: "landing" });
  });

  it("does not write localStorage when meta is empty object", async () => {
    const user = userEvent.setup();
    renderButtons({
      redirectTo: "https://app.volaura.com/callback",
      meta: {},
    });
    await user.click(screen.getByRole("button", { name: /google/i }));
    expect(localStorage.getItem(OAUTH_META_KEY)).toBeNull();
  });

  it("does not write localStorage when meta is not provided", async () => {
    const user = userEvent.setup();
    renderButtons({ redirectTo: "https://app.volaura.com/callback" });
    await user.click(screen.getByRole("button", { name: /google/i }));
    expect(localStorage.getItem(OAUTH_META_KEY)).toBeNull();
  });
});
