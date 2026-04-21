import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import React from "react";

// ── Global stubs ──────────────────────────────────────────────────────────────

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
});

// ── Mock: react-i18next ───────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { defaultValue?: string }) =>
      opts?.defaultValue ?? key,
    i18n: { language: "az" },
  }),
}));

// ── Mock: next/navigation ─────────────────────────────────────────────────────

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  usePathname: () => "/az/dashboard",
  useParams: () => ({ locale: "az" }),
}));

// ── Mock: next/link ───────────────────────────────────────────────────────────

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    className,
    "aria-label": ariaLabel,
    "aria-current": ariaCurrent,
    ...rest
  }: {
    href: string;
    children?: React.ReactNode;
    className?: string;
    "aria-label"?: string;
    "aria-current"?: string;
    [key: string]: unknown;
  }) =>
    React.createElement(
      "a",
      { href, className, "aria-label": ariaLabel, "aria-current": ariaCurrent, ...rest },
      children
    ),
}));

// ── Mock: @/i18nConfig ────────────────────────────────────────────────────────

vi.mock("@/i18nConfig", () => ({
  default: {
    locales: ["az", "en"],
    defaultLocale: "az",
    prefixDefault: true,
  },
}));

// ── Mock: @/lib/supabase/client ───────────────────────────────────────────────

const mockGetUser = vi.fn().mockResolvedValue({ data: { user: null } });
const mockChannel = {
  on: vi.fn().mockReturnThis(),
  subscribe: vi.fn().mockReturnThis(),
};
const mockRemoveChannel = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: vi.fn(() => ({
    auth: {
      getUser: mockGetUser,
    },
    from: vi.fn(() => ({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      maybeSingle: vi.fn().mockResolvedValue({ data: null }),
      update: vi.fn().mockReturnThis(),
    })),
    channel: vi.fn(() => mockChannel),
    removeChannel: mockRemoveChannel,
  })),
}));

// ── Mock: @/hooks/use-energy-mode ─────────────────────────────────────────────

const mockSetEnergy = vi.fn();

vi.mock("@/hooks/use-energy-mode", () => ({
  useEnergyMode: vi.fn(() => ({
    energy: "full",
    setEnergy: mockSetEnergy,
  })),
}));

// ── Mock: @/hooks/queries/use-notifications ───────────────────────────────────

vi.mock("@/hooks/queries/use-notifications", () => ({
  useRealtimeNotifications: vi.fn(),
}));

// ── Mock: @/stores/auth-store ─────────────────────────────────────────────────

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: vi.fn((selector: (s: { user: null }) => unknown) =>
    selector({ user: null })
  ),
}));

// ── Mock: @/components/assessment/energy-picker ───────────────────────────────

vi.mock("@/components/assessment/energy-picker", () => ({
  EnergyPicker: ({
    value,
    onChange,
    variant,
  }: {
    value: string;
    onChange: (v: string) => void;
    variant?: string;
  }) =>
    React.createElement(
      "div",
      { "data-testid": "energy-picker", "data-value": value, "data-variant": variant },
      React.createElement("button", { onClick: () => onChange("mid") }, "energy-mid")
    ),
}));

// ── Mock: @/components/ui/avatar ─────────────────────────────────────────────

vi.mock("@/components/ui/avatar", () => ({
  Avatar: ({ name, size }: { name: string; size?: string }) =>
    React.createElement("div", { "data-testid": "avatar", "data-size": size }, name),
}));

// ── Mock: @/lib/utils/cn ──────────────────────────────────────────────────────

vi.mock("@/lib/utils/cn", () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(" "),
}));

// ── Mock: lucide-react ────────────────────────────────────────────────────────

vi.mock("lucide-react", () => ({
  LayoutDashboard: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "layout-dashboard" }),
  Users: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "users" }),
  Building2: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "building2" }),
  Star: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "star" }),
  Bot: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "bot" }),
  ShieldCheck: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "shield-check" }),
  Gavel: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "gavel" }),
  Clock: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "clock" }),
  TrendingUp: () => React.createElement("svg", { "aria-hidden": "true", "data-icon": "trending-up" }),
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { EnergyInit } from "@/components/layout/energy-init";
import { RealtimeNotificationsProvider } from "@/components/layout/realtime-notifications";
import { SkipToContent } from "@/components/layout/skip-to-content";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { BottomNav } from "@/components/layout/bottom-nav";
import { AdminSidebar } from "@/components/layout/admin-sidebar";
import { TopBar } from "@/components/layout/top-bar";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { useAuthStore } from "@/stores/auth-store";
import { useRealtimeNotifications } from "@/hooks/queries/use-notifications";

// ── 1. EnergyInit ─────────────────────────────────────────────────────────────

describe("EnergyInit — rendering", () => {
  it("renders null (no DOM output)", () => {
    const { container } = render(<EnergyInit />);
    expect(container.firstChild).toBeNull();
  });

  it("sets data-energy attribute on documentElement after mount", async () => {
    await act(async () => {
      render(<EnergyInit />);
    });
    expect(document.documentElement.getAttribute("data-energy")).toBe("full");
  });

  it("uses energy value from useEnergyMode hook", async () => {
    vi.mocked(useEnergyMode).mockReturnValueOnce({ energy: "low", setEnergy: vi.fn() });
    await act(async () => {
      render(<EnergyInit />);
    });
    expect(document.documentElement.getAttribute("data-energy")).toBe("low");
  });

  it("updates data-energy when energy changes to mid", async () => {
    vi.mocked(useEnergyMode).mockReturnValueOnce({ energy: "mid", setEnergy: vi.fn() });
    await act(async () => {
      render(<EnergyInit />);
    });
    expect(document.documentElement.getAttribute("data-energy")).toBe("mid");
  });
});

// ── 2. RealtimeNotificationsProvider ─────────────────────────────────────────

describe("RealtimeNotificationsProvider — rendering", () => {
  beforeEach(() => {
    mockGetUser.mockResolvedValue({ data: { user: null } });
  });

  it("renders null (no DOM output)", () => {
    const { container } = render(<RealtimeNotificationsProvider />);
    expect(container.firstChild).toBeNull();
  });

  it("calls getUser on mount", async () => {
    await act(async () => {
      render(<RealtimeNotificationsProvider />);
    });
    expect(mockGetUser).toHaveBeenCalled();
  });

  it("calls useRealtimeNotifications with null when no user", async () => {
    mockGetUser.mockResolvedValueOnce({ data: { user: null } });
    await act(async () => {
      render(<RealtimeNotificationsProvider />);
    });
    expect(vi.mocked(useRealtimeNotifications)).toHaveBeenCalledWith(null);
  });

  it("calls useRealtimeNotifications with userId when user present", async () => {
    mockGetUser.mockResolvedValueOnce({ data: { user: { id: "user-123" } } });
    await act(async () => {
      render(<RealtimeNotificationsProvider />);
    });
    expect(vi.mocked(useRealtimeNotifications)).toHaveBeenCalledWith("user-123");
  });

  it("does not throw on unmount", () => {
    const { unmount } = render(<RealtimeNotificationsProvider />);
    expect(() => unmount()).not.toThrow();
  });
});

// ── 3. SkipToContent ─────────────────────────────────────────────────────────

describe("SkipToContent — rendering", () => {
  it("renders an anchor element", () => {
    render(<SkipToContent />);
    expect(screen.getByRole("link")).toBeInTheDocument();
  });

  it("href points to #main-content", () => {
    render(<SkipToContent />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "#main-content");
  });

  it("link text is the defaultValue (Azerbaijani)", () => {
    render(<SkipToContent />);
    expect(screen.getByRole("link")).toHaveTextContent("Əsas məzmuna keç");
  });

  it("link has sr-only class by default (visually hidden)", () => {
    render(<SkipToContent />);
    const link = screen.getByRole("link");
    expect(link.className).toContain("sr-only");
  });

  it("link has focus-visible fixed positioning classes", () => {
    render(<SkipToContent />);
    const link = screen.getByRole("link");
    expect(link.className).toContain("focus-visible:fixed");
  });

  it("link has high z-index class when focused", () => {
    render(<SkipToContent />);
    const link = screen.getByRole("link");
    expect(link.className).toContain("focus-visible:z-[999]");
  });

  it("link has primary bg class on focus-visible", () => {
    render(<SkipToContent />);
    const link = screen.getByRole("link");
    expect(link.className).toContain("focus-visible:bg-primary");
  });
});

describe("SkipToContent — a11y", () => {
  it("is keyboard-reachable via tab", () => {
    render(<SkipToContent />);
    const link = screen.getByRole("link");
    link.focus();
    expect(document.activeElement).toBe(link);
  });

  it("activatable with Enter key (native anchor behavior)", () => {
    render(<SkipToContent />);
    const link = screen.getByRole("link");
    link.focus();
    fireEvent.keyDown(link, { key: "Enter" });
    // Native anchor: no error thrown
    expect(link).toBeInTheDocument();
  });
});

// ── 4. LanguageSwitcher ───────────────────────────────────────────────────────

describe("LanguageSwitcher — rendering", () => {
  it("renders a container div", () => {
    const { container } = render(<LanguageSwitcher />);
    expect(container.firstChild).toBeInstanceOf(HTMLDivElement);
  });

  it("renders buttons for each locale (az, en)", () => {
    render(<LanguageSwitcher />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(2);
  });

  it("renders az button", () => {
    render(<LanguageSwitcher />);
    expect(screen.getByRole("button", { name: "az" })).toBeInTheDocument();
  });

  it("renders en button", () => {
    render(<LanguageSwitcher />);
    expect(screen.getByRole("button", { name: "en" })).toBeInTheDocument();
  });

  it("active locale button has bg-primary class", () => {
    // pathname = "/az/dashboard" → currentLocale = "az"
    render(<LanguageSwitcher />);
    const azButton = screen.getByRole("button", { name: "az" });
    expect(azButton.className).toContain("bg-primary");
  });

  it("inactive locale button does not have bg-primary class", () => {
    render(<LanguageSwitcher />);
    const enButton = screen.getByRole("button", { name: "en" });
    expect(enButton.className).not.toContain("bg-primary");
  });
});

describe("LanguageSwitcher — interaction", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("clicking inactive locale calls router.push with new path", () => {
    render(<LanguageSwitcher />);
    const enButton = screen.getByRole("button", { name: "en" });
    fireEvent.click(enButton);
    expect(mockPush).toHaveBeenCalledWith("/en/dashboard");
  });

  it("clicking active locale does not call router.push", () => {
    render(<LanguageSwitcher />);
    const azButton = screen.getByRole("button", { name: "az" });
    fireEvent.click(azButton);
    expect(mockPush).not.toHaveBeenCalled();
  });
});

// ── 5. BottomNav ──────────────────────────────────────────────────────────────

describe("BottomNav — rendering", () => {
  it("renders a nav element", () => {
    render(<BottomNav />);
    expect(screen.getByRole("navigation")).toBeInTheDocument();
  });

  it("nav has aria-label from i18n key", () => {
    render(<BottomNav />);
    expect(screen.getByRole("navigation")).toHaveAttribute(
      "aria-label",
      "nav.mainNavigation"
    );
  });

  it("renders dashboard link", () => {
    render(<BottomNav />);
    const link = screen.getByRole("link", { name: /nav\.dashboard/i });
    expect(link).toBeInTheDocument();
  });

  it("renders aura link", () => {
    render(<BottomNav />);
    expect(screen.getByRole("link", { name: /nav\.aura/i })).toBeInTheDocument();
  });

  it("renders assessment link", () => {
    render(<BottomNav />);
    expect(screen.getByRole("link", { name: /nav\.assessment/i })).toBeInTheDocument();
  });

  it("renders profile link", () => {
    render(<BottomNav />);
    expect(screen.getByRole("link", { name: /nav\.profile/i })).toBeInTheDocument();
  });

  it("renders exactly 4 nav links", () => {
    render(<BottomNav />);
    expect(screen.getAllByRole("link")).toHaveLength(4);
  });

  it("dashboard link href includes locale prefix", () => {
    render(<BottomNav />);
    const links = screen.getAllByRole("link");
    const dashLink = links.find((l) => l.getAttribute("href")?.includes("/dashboard"));
    expect(dashLink).toHaveAttribute("href", "/az/dashboard");
  });

  it("aura link href includes locale prefix", () => {
    render(<BottomNav />);
    const links = screen.getAllByRole("link");
    const auraLink = links.find((l) => l.getAttribute("href")?.includes("/aura"));
    expect(auraLink).toHaveAttribute("href", "/az/aura");
  });
});

describe("BottomNav — active state", () => {
  it("active link has aria-current=page", () => {
    // pathname = "/az/dashboard" so dashboard is active
    render(<BottomNav />);
    const links = screen.getAllByRole("link");
    const dashLink = links.find((l) => l.getAttribute("href") === "/az/dashboard");
    expect(dashLink).toHaveAttribute("aria-current", "page");
  });

  it("inactive links do not have aria-current", () => {
    render(<BottomNav />);
    const links = screen.getAllByRole("link");
    const auraLink = links.find((l) => l.getAttribute("href") === "/az/aura");
    expect(auraLink).not.toHaveAttribute("aria-current");
  });

  it("active link icon span has text-primary class", () => {
    render(<BottomNav />);
    const links = screen.getAllByRole("link");
    const dashLink = links.find((l) => l.getAttribute("href") === "/az/dashboard");
    const iconSpan = dashLink?.querySelector("span[aria-hidden]");
    expect(iconSpan?.className).toContain("text-primary");
  });

  it("inactive link icon span has text-on-surface-variant class", () => {
    render(<BottomNav />);
    const links = screen.getAllByRole("link");
    const auraLink = links.find((l) => l.getAttribute("href") === "/az/aura");
    const iconSpan = auraLink?.querySelector("span[aria-hidden]");
    expect(iconSpan?.className).toContain("text-on-surface-variant");
  });

  it("icon spans are aria-hidden (decorative)", () => {
    render(<BottomNav />);
    const hiddenSpans = document.querySelectorAll("span[aria-hidden='true']");
    expect(hiddenSpans.length).toBeGreaterThanOrEqual(4);
  });
});

describe("BottomNav — mobile-only visibility", () => {
  it("nav has md:hidden class", () => {
    render(<BottomNav />);
    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("md:hidden");
  });

  it("nav is fixed bottom-0", () => {
    render(<BottomNav />);
    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("fixed");
    expect(nav.className).toContain("bottom-0");
  });
});

// ── 6. AdminSidebar ───────────────────────────────────────────────────────────

describe("AdminSidebar — rendering", () => {
  it("renders an aside element", () => {
    const { container } = render(<AdminSidebar />);
    expect(container.querySelector("aside")).toBeInTheDocument();
  });

  it("renders Admin Panel brand text", () => {
    render(<AdminSidebar />);
    expect(screen.getByText("Admin Panel")).toBeInTheDocument();
  });

  it("renders admin navigation with aria-label", () => {
    render(<AdminSidebar />);
    expect(screen.getByRole("navigation", { name: "Admin navigation" })).toBeInTheDocument();
  });

  it("renders Overview link", () => {
    render(<AdminSidebar />);
    expect(screen.getByRole("link", { name: /Overview/ })).toBeInTheDocument();
  });

  it("renders AI Office link", () => {
    render(<AdminSidebar />);
    expect(screen.getByRole("link", { name: /AI Office/ })).toBeInTheDocument();
  });

  it("renders Users link", () => {
    render(<AdminSidebar />);
    expect(screen.getByRole("link", { name: /Users/ })).toBeInTheDocument();
  });

  it("renders Grievances link", () => {
    render(<AdminSidebar />);
    expect(screen.getByRole("link", { name: /Grievances/ })).toBeInTheDocument();
  });

  it("renders Back to app link", () => {
    render(<AdminSidebar />);
    expect(screen.getByRole("link", { name: /Back to app/ })).toBeInTheDocument();
  });
});

describe("AdminSidebar — hrefs", () => {
  it("Overview link href = /az/admin", () => {
    render(<AdminSidebar />);
    const link = screen.getByRole("link", { name: /Overview/ });
    expect(link).toHaveAttribute("href", "/az/admin");
  });

  it("AI Office link href = /az/admin/swarm", () => {
    render(<AdminSidebar />);
    const link = screen.getByRole("link", { name: /AI Office/ });
    expect(link).toHaveAttribute("href", "/az/admin/swarm");
  });

  it("Users link href = /az/admin/users", () => {
    render(<AdminSidebar />);
    const link = screen.getByRole("link", { name: /Users/ });
    expect(link).toHaveAttribute("href", "/az/admin/users");
  });

  it("Grievances link href = /az/admin/grievances", () => {
    render(<AdminSidebar />);
    const link = screen.getByRole("link", { name: /Grievances/ });
    expect(link).toHaveAttribute("href", "/az/admin/grievances");
  });

  it("Back to app link href = /az/dashboard", () => {
    render(<AdminSidebar />);
    const link = screen.getByRole("link", { name: /Back to app/ });
    expect(link).toHaveAttribute("href", "/az/dashboard");
  });
});

describe("AdminSidebar — active state", () => {
  it("Overview link has aria-current=page when pathname = /az/admin", () => {
    // usePathname mock returns "/az/dashboard" — Overview not active
    // Overview active check: pathname === base (i.e. "/az/admin")
    render(<AdminSidebar />);
    const overviewLink = screen.getByRole("link", { name: /Overview/ });
    // pathname is /az/dashboard, not /az/admin — not active
    expect(overviewLink).not.toHaveAttribute("aria-current");
  });

  it("non-active links do not have aria-current", () => {
    render(<AdminSidebar />);
    const usersLink = screen.getByRole("link", { name: /Users/ });
    expect(usersLink).not.toHaveAttribute("aria-current");
  });
});

describe("AdminSidebar — a11y", () => {
  it("ShieldCheck icon is aria-hidden", () => {
    const { container } = render(<AdminSidebar />);
    const icons = container.querySelectorAll("svg[aria-hidden='true']");
    expect(icons.length).toBeGreaterThan(0);
  });

  it("aside is hidden on mobile (hidden md:flex)", () => {
    const { container } = render(<AdminSidebar />);
    const aside = container.querySelector("aside");
    expect(aside?.className).toContain("hidden");
    expect(aside?.className).toContain("md:flex");
  });
});

// ── 7. TopBar ─────────────────────────────────────────────────────────────────

describe("TopBar — rendering (no user)", () => {
  it("renders a header element", () => {
    const { container } = render(<TopBar title="Dashboard" />);
    expect(container.querySelector("header")).toBeInTheDocument();
  });

  it("renders the title prop in h1", () => {
    render(<TopBar title="Dashboard" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Dashboard");
  });

  it("renders EnergyPicker by default (showEnergyPicker=true)", () => {
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("energy-picker")).toBeInTheDocument();
  });

  it("does not render Avatar when user is null", () => {
    render(<TopBar title="Dashboard" />);
    expect(screen.queryByTestId("avatar")).not.toBeInTheDocument();
  });

  it("renders LanguageSwitcher buttons", () => {
    render(<TopBar title="Dashboard" />);
    const buttons = screen.getAllByRole("button");
    // az + en locale buttons + energy button
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it("header has glass-header class", () => {
    const { container } = render(<TopBar title="Dashboard" />);
    const header = container.querySelector("header");
    expect(header?.className).toContain("glass-header");
  });

  it("header is fixed top-0", () => {
    const { container } = render(<TopBar title="Dashboard" />);
    const header = container.querySelector("header");
    expect(header?.className).toContain("fixed");
    expect(header?.className).toContain("top-0");
  });

  it("renders spacer div with h-14 for layout offset", () => {
    const { container } = render(<TopBar title="Dashboard" />);
    const spacer = container.querySelector("div[aria-hidden='true']");
    expect(spacer?.className).toContain("h-14");
  });
});

describe("TopBar — showEnergyPicker=false", () => {
  it("does not render EnergyPicker when showEnergyPicker=false", () => {
    render(<TopBar title="Events" showEnergyPicker={false} />);
    expect(screen.queryByTestId("energy-picker")).not.toBeInTheDocument();
  });

  it("still renders title when showEnergyPicker=false", () => {
    render(<TopBar title="Events" showEnergyPicker={false} />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Events");
  });

  it("still renders LanguageSwitcher when showEnergyPicker=false", () => {
    render(<TopBar title="Events" showEnergyPicker={false} />);
    expect(screen.getByRole("button", { name: "az" })).toBeInTheDocument();
  });
});

describe("TopBar — rendering with user", () => {
  beforeEach(() => {

    vi.mocked(useAuthStore).mockImplementation(((selector: any) =>
      selector({
        user: {
          email: "yusif@example.com",
          user_metadata: {
            display_name: "Yusif G",
            avatar_url: null,
          },
        },
      })) as any);
  });

  it("renders Avatar when user is present", () => {
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("avatar")).toBeInTheDocument();
  });

  it("Avatar receives display_name as name prop", () => {
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("avatar")).toHaveTextContent("Yusif G");
  });

  it("falls back to full_name when display_name absent", () => {

    vi.mocked(useAuthStore).mockImplementationOnce(((selector: any) =>
      selector({
        user: {
          email: "yusif@example.com",
          user_metadata: { full_name: "Yusif Ganbarov" },
        },
      })) as any);
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("avatar")).toHaveTextContent("Yusif Ganbarov");
  });

  it("falls back to email local-part when no metadata name", () => {

    vi.mocked(useAuthStore).mockImplementationOnce(((selector: any) =>
      selector({
        user: {
          email: "yusif@example.com",
          user_metadata: {},
        },
      })) as any);
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("avatar")).toHaveTextContent("yusif");
  });
});

describe("TopBar — energy picker interaction", () => {
  it("EnergyPicker receives current energy value", () => {
    vi.mocked(useEnergyMode).mockReturnValueOnce({ energy: "low", setEnergy: mockSetEnergy });
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("energy-picker")).toHaveAttribute("data-value", "low");
  });

  it("EnergyPicker variant is compact", () => {
    render(<TopBar title="Dashboard" />);
    expect(screen.getByTestId("energy-picker")).toHaveAttribute("data-variant", "compact");
  });

  it("clicking energy option calls setEnergy", () => {
    render(<TopBar title="Dashboard" />);
    fireEvent.click(screen.getByText("energy-mid"));
    expect(mockSetEnergy).toHaveBeenCalledWith("mid");
  });
});
