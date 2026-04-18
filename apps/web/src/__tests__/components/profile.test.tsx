import { describe, it, expect, vi, beforeEach, afterEach, beforeAll } from "vitest";
import { render, screen, waitFor, act, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Global browser API stubs ──────────────────────────────────────────────────

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb: FrameRequestCallback) =>
      setTimeout(cb, 16) as unknown as number;
    window.cancelAnimationFrame = (id: number) => clearTimeout(id);
  }

  // Define clipboard once as configurable so userEvent can redefine it
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    writable: true,
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
});

// ── Mock: react-i18next ───────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { defaultValue?: string; name?: string }) => {
      if (opts?.defaultValue) return opts.defaultValue;
      // Simulate translation keys that have no defaultValue
      return key;
    },
    i18n: { language: "en" },
  }),
}));

// ── Mock: next/navigation ─────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/en",
}));

// ── Mock: @/lib/supabase/client ───────────────────────────────────────────────

const mockGetSession = vi.fn();
vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
  }),
}));

// ── Mock: @/lib/api/client ────────────────────────────────────────────────────

const mockApiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  API_BASE: "/api",
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    detail: string;
    constructor(status: number, code: string, detail: string) {
      super(detail);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
      this.detail = detail;
    }
  },
}));

// ── Mock: @/hooks/use-focus-trap ─────────────────────────────────────────────

vi.mock("@/hooks/use-focus-trap", () => ({
  useFocusTrap: () => ({ current: null }),
}));

// ── Mock: @/hooks/queries/use-organizations ──────────────────────────────────

const mockUseMyOrganization = vi.fn();
const mockMutationMutate = vi.fn();
const mockUseCreateIntroRequest = vi.fn();

vi.mock("@/hooks/queries/use-organizations", () => ({
  useMyOrganization: () => mockUseMyOrganization(),
  useCreateIntroRequest: () => mockUseCreateIntroRequest(),
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { ChallengeButton } from "@/components/profile/challenge-button";
import { ProfileViewTracker } from "@/components/profile/profile-view-tracker";
import { IntroRequestButton } from "@/components/profile/intro-request-button";

// ── 1. ChallengeButton ────────────────────────────────────────────────────────

describe("ChallengeButton — rendering", () => {
  it("renders a button element", () => {
    render(<ChallengeButton username="alice" />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("shows challenge peer text by default", () => {
    render(<ChallengeButton username="alice" />);
    expect(screen.getByRole("button")).toHaveTextContent("profile.challengePeer");
  });

  it("button type is button (not submit)", () => {
    render(<ChallengeButton username="alice" />);
    expect(screen.getByRole("button")).toHaveAttribute("type", "button");
  });

  it("renders Share2 icon with aria-hidden", () => {
    const { container } = render(<ChallengeButton username="alice" />);
    const icon = container.querySelector('svg[aria-hidden="true"]');
    expect(icon).toBeInTheDocument();
  });

  it("has min-h-[44px] for touch target compliance", () => {
    render(<ChallengeButton username="alice" />);
    expect(screen.getByRole("button").className).toContain("min-h-[44px]");
  });
});

describe("ChallengeButton — clipboard interaction", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Reset the clipboard mock before each test
    (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("writes correct URL to clipboard on click", async () => {
    render(<ChallengeButton username="alice" />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button"));
    });
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      "https://volaura.app/?ref=alice"
    );
  });

  it("shows copied text after click", async () => {
    render(<ChallengeButton username="alice" />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button"));
    });
    expect(screen.getByRole("button")).toHaveTextContent("profile.challengeLink");
  });

  it("reverts to original text after 2500ms", async () => {
    render(<ChallengeButton username="alice" />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button"));
    });
    await act(async () => {
      vi.advanceTimersByTime(2500);
    });
    expect(screen.getByRole("button")).toHaveTextContent("profile.challengePeer");
  });

  it("uses username prop in clipboard URL", async () => {
    render(<ChallengeButton username="bob123" />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button"));
    });
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      "https://volaura.app/?ref=bob123"
    );
  });

  it("shows default peer text before interaction", () => {
    render(<ChallengeButton username="charlie" />);
    expect(screen.getByRole("button")).toHaveTextContent("profile.challengePeer");
  });
});

// ── 2. ProfileViewTracker ─────────────────────────────────────────────────────

describe("ProfileViewTracker — rendering", () => {
  beforeEach(() => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    mockApiFetch.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders null (no visible output)", async () => {
    const { container } = render(<ProfileViewTracker username="alice" />);
    await act(async () => {});
    expect(container.firstChild).toBeNull();
  });

  it("does not call apiFetch when no session", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    await act(async () => {
      render(<ProfileViewTracker username="alice" />);
    });
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("calls apiFetch POST view when session exists", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok123" } },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({}));

    await act(async () => {
      render(<ProfileViewTracker username="alice" />);
    });
    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/api/profiles/alice/view",
        expect.objectContaining({ method: "POST", token: "tok123" })
      );
    });
  });

  it("fires analytics event when session exists", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok456" } },
    });
    const mockFetch = vi.fn().mockResolvedValue({});
    vi.stubGlobal("fetch", mockFetch);

    await act(async () => {
      render(<ProfileViewTracker username="bob" />);
    });
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/analytics/event"),
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  it("analytics event body contains viewed_username", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok789" } },
    });
    const mockFetch = vi.fn().mockResolvedValue({});
    vi.stubGlobal("fetch", mockFetch);

    await act(async () => {
      render(<ProfileViewTracker username="charlie" />);
    });
    await waitFor(() => {
      const call = mockFetch.mock.calls.find((c) =>
        String(c[0]).includes("/analytics/event")
      );
      expect(call).toBeDefined();
      const body = JSON.parse(call[1].body);
      expect(body.properties.viewed_username).toBe("charlie");
    });
  });

  it("swallows errors — does not throw on supabase failure", async () => {
    mockGetSession.mockRejectedValue(new Error("supabase down"));
    await expect(
      act(async () => {
        render(<ProfileViewTracker username="alice" />);
      })
    ).resolves.not.toThrow();
  });

  it("swallows errors — does not throw on apiFetch failure", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok" } },
    });
    mockApiFetch.mockRejectedValue(new Error("api down"));
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({}));

    await expect(
      act(async () => {
        render(<ProfileViewTracker username="alice" />);
      })
    ).resolves.not.toThrow();
  });

  it("uses username prop in view endpoint URL", async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok" } },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({}));

    await act(async () => {
      render(<ProfileViewTracker username="specificuser" />);
    });
    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/api/profiles/specificuser/view",
        expect.anything()
      );
    });
  });
});

// ── 3. IntroRequestButton ─────────────────────────────────────────────────────

const defaultMutation = {
  mutate: mockMutationMutate,
  isPending: false,
  isSuccess: false,
  isError: false,
};

describe("IntroRequestButton — no org (returns null)", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: undefined });
    mockUseCreateIntroRequest.mockReturnValue(defaultMutation);
  });

  it("renders nothing when org is undefined", () => {
    const { container } = render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when org is null", () => {
    mockUseMyOrganization.mockReturnValue({ data: null });
    const { container } = render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    expect(container.firstChild).toBeNull();
  });
});

describe("IntroRequestButton — org user: initial rendering", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
    mockUseCreateIntroRequest.mockReturnValue(defaultMutation);
  });

  it("renders Request Introduction button", () => {
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    expect(screen.getByRole("button", { name: "Request Introduction" })).toBeInTheDocument();
  });

  it("does not show dialog initially", () => {
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("does not show toast initially", () => {
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});

describe("IntroRequestButton — modal open/close", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
  });

  it("opens dialog when Request Introduction clicked", async () => {
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("dialog has aria-modal=true", async () => {
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("dialog has aria-labelledby pointing to title id", async () => {
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-labelledby", "intro-modal-title");
    expect(document.getElementById("intro-modal-title")).toBeInTheDocument();
  });

  it("shows professionalName in modal subtitle", async () => {
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    expect(screen.getByText(`Send a project intro to Alice`)).toBeInTheDocument();
  });

  it("closes dialog when Cancel clicked", async () => {
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes dialog when backdrop clicked", async () => {
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Request Introduction" })); });
    const backdrop = document.querySelector(".fixed.inset-0.z-40") as HTMLElement;
    // Simulate backdrop click with target === currentTarget (direct click on backdrop)
    act(() => {
      fireEvent.click(backdrop, { bubbles: true });
    });
    // The backdrop's onClick checks e.target === e.currentTarget
    // Since JSDOM's fireEvent.click on the backdrop sets target=backdrop, this closes the dialog
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("resets form fields on close", () => {
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Request Introduction" })); });
    const projectInput = screen.getByLabelText(/Project name/i);
    act(() => { fireEvent.change(projectInput, { target: { value: "My Project" } }); });
    expect(projectInput).toHaveValue("My Project");
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Cancel" })); });
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Request Introduction" })); });
    expect(screen.getByLabelText(/Project name/i)).toHaveValue("");
  });
});

describe("IntroRequestButton — form fields", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
  });

  async function openModal() {
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    return user;
  }

  it("renders project name input with label", async () => {
    await openModal();
    expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument();
  });

  it("project name input is required", async () => {
    await openModal();
    expect(screen.getByLabelText(/Project name/i)).toHaveAttribute("required");
  });

  it("project name input has maxLength 200", async () => {
    await openModal();
    expect(screen.getByLabelText(/Project name/i)).toHaveAttribute("maxLength", "200");
  });

  it("renders timeline select", async () => {
    await openModal();
    expect(screen.getByLabelText(/Timeline/i)).toBeInTheDocument();
  });

  it("timeline select defaults to normal", async () => {
    await openModal();
    expect(screen.getByLabelText(/Timeline/i)).toHaveValue("normal");
  });

  it("timeline select has three options", async () => {
    await openModal();
    const options = screen.getAllByRole("option");
    const values = options.map((o) => (o as HTMLOptionElement).value);
    expect(values).toContain("urgent");
    expect(values).toContain("normal");
    expect(values).toContain("flexible");
  });

  it("renders message textarea with label", async () => {
    await openModal();
    expect(screen.getByLabelText(/Message/i)).toBeInTheDocument();
  });

  it("message textarea has maxLength 500", async () => {
    await openModal();
    expect(screen.getByLabelText(/Message/i)).toHaveAttribute("maxLength", "500");
  });

  it("shows character count 0/500 initially", async () => {
    await openModal();
    expect(screen.getByText("0/500")).toBeInTheDocument();
  });

  it("updates character count as user types in message", async () => {
    const user = await openModal();
    await user.type(screen.getByLabelText(/Message/i), "Hello");
    expect(screen.getByText("5/500")).toBeInTheDocument();
  });

  it("shows (optional) label next to message", async () => {
    await openModal();
    expect(screen.getByText("(optional)")).toBeInTheDocument();
  });

  it("required asterisk has aria-hidden on project name label", async () => {
    await openModal();
    const { container } = await (async () => ({ container: document.body }))();
    const asterisk = container.querySelector(
      'label[for="intro-project"] span[aria-hidden="true"]'
    );
    expect(asterisk).toBeInTheDocument();
  });
});

describe("IntroRequestButton — submit button state", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
  });

  it("Send Request button is disabled when project name empty", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    expect(screen.getByRole("button", { name: "Send Request" })).toBeDisabled();
  });

  it("Send Request button enabled when project name has text", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "Test Project");
    expect(screen.getByRole("button", { name: "Send Request" })).not.toBeDisabled();
  });

  it("shows Sending… when mutation isPending", async () => {
    mockUseCreateIntroRequest.mockReturnValue({
      ...defaultMutation,
      isPending: true,
    });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "Test");
    expect(screen.getByRole("button", { name: "Sending…" })).toBeDisabled();
  });

  it("submit button disabled when isPending even with project name", async () => {
    mockUseCreateIntroRequest.mockReturnValue({
      ...defaultMutation,
      isPending: true,
    });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "Test");
    expect(screen.getByRole("button", { name: "Sending…" })).toHaveAttribute("disabled");
  });
});

describe("IntroRequestButton — form submission", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
    mockMutationMutate.mockReset();
  });

  it("does not call mutate when project name is empty", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    fireEvent.submit(document.querySelector("form")!);
    expect(mockMutationMutate).not.toHaveBeenCalled();
  });

  it("calls mutate with correct payload on submit", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "My Project");
    await user.click(screen.getByRole("button", { name: "Send Request" }));
    expect(mockMutationMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        professional_id: "p1",
        project_name: "My Project",
        timeline: "normal",
      }),
      expect.any(Object)
    );
  });

  it("trims whitespace from project name before submit", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "  My Project  ");
    await user.click(screen.getByRole("button", { name: "Send Request" }));
    expect(mockMutationMutate).toHaveBeenCalledWith(
      expect.objectContaining({ project_name: "My Project" }),
      expect.any(Object)
    );
  });

  it("passes selected timeline to mutate", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "Project X");
    await user.selectOptions(screen.getByLabelText(/Timeline/i), "urgent");
    await user.click(screen.getByRole("button", { name: "Send Request" }));
    expect(mockMutationMutate).toHaveBeenCalledWith(
      expect.objectContaining({ timeline: "urgent" }),
      expect.any(Object)
    );
  });

  it("passes message to mutate when provided", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "Project Y");
    await user.type(screen.getByLabelText(/Message/i), "Looking forward to working with you");
    await user.click(screen.getByRole("button", { name: "Send Request" }));
    expect(mockMutationMutate).toHaveBeenCalledWith(
      expect.objectContaining({ message: "Looking forward to working with you" }),
      expect.any(Object)
    );
  });

  it("omits message from payload when message is empty", async () => {
    mockUseCreateIntroRequest.mockReturnValue({ ...defaultMutation, mutate: mockMutationMutate });
    const user = userEvent.setup();
    render(
      <IntroRequestButton professionalId="p1" professionalName="Alice" />
    );
    await user.click(screen.getByRole("button", { name: "Request Introduction" }));
    await user.type(screen.getByLabelText(/Project name/i), "Project Z");
    await user.click(screen.getByRole("button", { name: "Send Request" }));
    expect(mockMutationMutate).toHaveBeenCalledWith(
      expect.objectContaining({ message: undefined }),
      expect.any(Object)
    );
  });
});

describe("IntroRequestButton — onSuccess handling", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
  });

  function renderAndTriggerSuccess() {
    mockUseCreateIntroRequest.mockReturnValue({
      ...defaultMutation,
      mutate: (_payload: unknown, opts: { onSuccess: () => void }) => opts.onSuccess(),
    });
    render(<IntroRequestButton professionalId="p1" professionalName="Alice" />);
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Request Introduction" })); });
    act(() => { fireEvent.change(screen.getByLabelText(/Project name/i), { target: { value: "Project A" } }); });
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Send Request" })); });
  }

  it("closes modal on success", () => {
    renderAndTriggerSuccess();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows success toast after submit", () => {
    renderAndTriggerSuccess();
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Introduction request sent!");
  });

  it("success toast has aria-live=polite", () => {
    renderAndTriggerSuccess();
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });

  it("success toast disappears after 4000ms", () => {
    vi.useFakeTimers();
    renderAndTriggerSuccess();
    act(() => { vi.advanceTimersByTime(4001); });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    vi.useRealTimers();
  });
});

describe("IntroRequestButton — onError handling", () => {
  beforeEach(() => {
    mockUseMyOrganization.mockReturnValue({ data: { id: "org1", name: "ACME" } });
  });

  function makeErrorMutation(status: number) {
    // Inline ApiError to avoid async import issues
    class ApiError extends Error {
      status: number; code: string; detail: string;
      constructor(s: number, c: string, d: string) { super(d); this.status = s; this.code = c; this.detail = d; }
    }
    mockUseCreateIntroRequest.mockReturnValue({
      ...defaultMutation,
      mutate: (
        _payload: unknown,
        opts: { onError: (err: unknown) => void }
      ) => opts.onError(new ApiError(status, status === 409 ? "CONFLICT" : "INTERNAL", "error")),
    });
  }

  function renderAndTriggerError(status: number) {
    makeErrorMutation(status);
    render(<IntroRequestButton professionalId="p1" professionalName="Alice" />);
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Request Introduction" })); });
    act(() => { fireEvent.change(screen.getByLabelText(/Project name/i), { target: { value: "Project B" } }); });
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Send Request" })); });
  }

  it("shows generic error toast on non-409 error", () => {
    renderAndTriggerError(500);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Failed to send request. Please try again."
    );
  });

  it("shows already-sent toast on 409 error", () => {
    renderAndTriggerError(409);
    expect(screen.getByRole("status")).toHaveTextContent(
      "You already sent a request to this professional."
    );
  });

  it("error toast disappears after 5000ms", () => {
    vi.useFakeTimers();
    renderAndTriggerError(500);
    expect(screen.getByRole("status")).toBeInTheDocument();
    act(() => { vi.advanceTimersByTime(5001); });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    vi.useRealTimers();
  });

  it("modal stays open on error", () => {
    renderAndTriggerError(500);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});
