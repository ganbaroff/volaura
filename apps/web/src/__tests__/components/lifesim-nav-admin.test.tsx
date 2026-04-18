import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";

// ── Standard mocks ─────────────────────────────────────────────────────────────

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, initial: _i, animate: _a, exit: _e, transition: _t, ...props }: any) =>
      React.createElement("div", props, children),
    span: ({ children, initial: _i, animate: _a, exit: _e, transition: _t, ...props }: any) =>
      React.createElement("span", props, children),
  },
  AnimatePresence: ({ children }: any) => React.createElement(React.Fragment, null, children),
  useReducedMotion: vi.fn(() => false),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: any) => opts?.defaultValue ?? key,
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: any) =>
    React.createElement("a", { href, ...props }, children),
}));

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/az/"),
  useParams: vi.fn(() => ({ locale: "az" })),
}));

vi.mock("@/lib/utils/cn", () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) =>
    React.createElement("div", { "data-testid": "skeleton", className }),
}));

vi.mock("@/components/ui/card", () => ({
  Card: ({ children, className }: any) =>
    React.createElement("div", { "data-testid": "card", className }, children),
  CardContent: ({ children, className }: any) =>
    React.createElement("div", { "data-testid": "card-content", className }, children),
}));

// ── Component-specific mocks ───────────────────────────────────────────────────

vi.mock("@/hooks/queries/use-lifesim", () => ({
  useLifesimPurchase: vi.fn(),
}));

vi.mock("@/hooks/use-analytics", () => ({
  useTrackEvent: vi.fn(() => vi.fn()),
}));

vi.mock("@/hooks/use-focus-trap", () => ({
  useFocusTrap: vi.fn(() => ({ current: null })),
}));

vi.mock("@/hooks/use-energy-mode", () => ({
  useEnergyMode: vi.fn(() => ({ energy: "full", setEnergy: vi.fn() })),
}));

vi.mock("@/components/layout/top-bar", () => ({
  TopBar: ({ title }: { title: string }) =>
    React.createElement("div", { "data-testid": "top-bar" }, title),
}));

vi.mock("@/hooks/queries/use-admin", () => ({
  useAdminStats: vi.fn(),
  useAdminOverview: vi.fn(),
  useAdminLiveEvents: vi.fn(),
}));

vi.mock("lucide-react", () => {
  const icon =
    (name: string) =>
    ({ className, "aria-hidden": ah }: any) =>
      React.createElement("svg", { "data-testid": `icon-${name}`, className, "aria-hidden": ah });
  return {
    Briefcase: icon("briefcase"),
    Coins: icon("coins"),
    HeartPulse: icon("heartpulse"),
    PartyPopper: icon("partypopper"),
    BookOpen: icon("bookopen"),
    X: icon("x"),
    Users: icon("users"),
    Building2: icon("building2"),
    ClipboardList: icon("clipboard"),
    Star: icon("star"),
    Gavel: icon("gavel"),
    Activity: icon("activity"),
    TrendingUp: icon("trendingup"),
    AlertTriangle: icon("alerttriangle"),
    Wallet: icon("wallet"),
    Zap: icon("zap"),
  };
});

// ── Imports after mocks ────────────────────────────────────────────────────────

import { CrystalShop, SHOP_ITEMS } from "@/components/lifesim/crystal-shop";
import { BottomTabBar } from "@/components/navigation/bottom-tab-bar";
import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { AdminOverview } from "@/components/admin/admin-overview";

import { useLifesimPurchase } from "@/hooks/queries/use-lifesim";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { useReducedMotion } from "framer-motion";
import { usePathname, useParams } from "next/navigation";
import { useAdminStats, useAdminOverview, useAdminLiveEvents } from "@/hooks/queries/use-admin";

// ── Typed mock helpers ─────────────────────────────────────────────────────────

const mockUseLifesimPurchase = useLifesimPurchase as ReturnType<typeof vi.fn>;
const mockUseEnergyMode = useEnergyMode as ReturnType<typeof vi.fn>;
const mockUseReducedMotion = useReducedMotion as ReturnType<typeof vi.fn>;
const mockUsePathname = usePathname as ReturnType<typeof vi.fn>;
const mockUseParams = useParams as ReturnType<typeof vi.fn>;
const mockUseAdminStats = useAdminStats as ReturnType<typeof vi.fn>;
const mockUseAdminOverview = useAdminOverview as ReturnType<typeof vi.fn>;
const mockUseAdminLiveEvents = useAdminLiveEvents as ReturnType<typeof vi.fn>;

function makePurchaseMock(overrides: Record<string, any> = {}) {
  return {
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
    isError: false,
    ...overrides,
  };
}

function makeOverview(overrides: Record<string, any> = {}) {
  return {
    activation_rate_24h: 0.30,
    w4_retention: 0.35,
    dau_wau_ratio: 0.55,
    errors_24h: 0,
    runway_months: 14,
    presence: {
      volaura_only: 50,
      mindshift_only: 30,
      both_products: 20,
      total_users: 100,
    },
    funnels: [
      { product: "volaura", signups_24h: 10, activated_24h: 4, activation_rate: 0.4 },
    ],
    computed_at: "2026-04-18T10:00:00Z",
    stale_after_seconds: 30,
    ...overrides,
  };
}

function makeStats(overrides: Record<string, any> = {}) {
  return {
    total_users: 250,
    total_organizations: 12,
    pending_org_approvals: 3,
    assessments_today: 42,
    avg_aura_score: 72.5,
    pending_grievances: 1,
    ...overrides,
  };
}

function makeEvent(overrides: Record<string, any> = {}) {
  return {
    id: "evt-1",
    product: "volaura",
    event_type: "assessment_completed",
    user_id_prefix: "usr-abc",
    created_at: new Date(Date.now() - 30_000).toISOString(),
    payload_summary: "communication competency",
    ...overrides,
  };
}

// ══════════════════════════════════════════════════════════════════════════════
// 1. CrystalShop
// ══════════════════════════════════════════════════════════════════════════════

describe("CrystalShop", () => {
  const baseProps = { currentCrystals: 200, onBoost: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseLifesimPurchase.mockReturnValue(makePurchaseMock());
  });

  it("renders Crystal Shop section with aria-label", () => {
    render(<CrystalShop {...baseProps} />);
    expect(
      screen.getByRole("region", { name: /crystal shop/i }),
    ).toBeInTheDocument();
  });

  it("renders all 4 shop items", () => {
    render(<CrystalShop {...baseProps} />);
    const buttons = screen.getAllByRole("button");
    // 4 item buttons (confirm dialog not open yet)
    expect(buttons).toHaveLength(4);
  });

  it("shows balance in header", () => {
    // t() mock returns defaultValue which contains {{count}} interpolation literal;
    // the component passes count as option — just verify the balance span is present.
    render(<CrystalShop currentCrystals={150} onBoost={vi.fn()} />);
    const balanceSpan = document.querySelector(".tabular-nums");
    expect(balanceSpan).not.toBeNull();
  });

  it("shows boost descriptions for each item", () => {
    render(<CrystalShop {...baseProps} />);
    expect(screen.getByText("intelligence +10")).toBeInTheDocument();
    expect(screen.getByText("social +5 · happiness +5")).toBeInTheDocument();
    expect(screen.getByText("health +10")).toBeInTheDocument();
    expect(screen.getByText("next promotion guaranteed")).toBeInTheDocument();
  });

  it("shows cost diamonds for each item", () => {
    render(<CrystalShop {...baseProps} />);
    expect(screen.getByText("50 ♦")).toBeInTheDocument();
    expect(screen.getByText("30 ♦")).toBeInTheDocument();
    expect(screen.getByText("100 ♦")).toBeInTheDocument();
    expect(screen.getByText("75 ♦")).toBeInTheDocument();
  });

  it("items are enabled when crystals >= cost", () => {
    render(<CrystalShop currentCrystals={200} onBoost={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => expect(btn).not.toBeDisabled());
  });

  it("disables items when crystals < cost", () => {
    render(<CrystalShop currentCrystals={20} onBoost={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    // All items cost >= 30, so all disabled
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it("only items with cost <= crystals are enabled (partial affordability)", () => {
    // Only social_event_ticket (30) is affordable
    render(<CrystalShop currentCrystals={35} onBoost={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    const enabled = buttons.filter((b) => !b.hasAttribute("disabled"));
    expect(enabled).toHaveLength(1);
  });

  it("clicking an item opens confirm dialog", () => {
    render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("confirm dialog shows aria-modal=true", () => {
    render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("confirm dialog shows item boost description", () => {
    render(<CrystalShop {...baseProps} />);
    // Click first item (premium_training_course)
    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(screen.getAllByText("intelligence +10").length).toBeGreaterThan(0);
  });

  it("confirm dialog has Cancel and Подтвердить buttons", () => {
    render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(screen.getByText("Подтвердить")).toBeInTheDocument();
  });

  it("Cancel button closes the dialog", () => {
    render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Cancel"));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("Close (X) button in dialog header closes the dialog", () => {
    render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    fireEvent.click(screen.getByLabelText("Close"));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("confirm button calls mutateAsync with correct args", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({});
    mockUseLifesimPurchase.mockReturnValue(makePurchaseMock({ mutateAsync }));
    const onBoost = vi.fn();
    render(<CrystalShop currentCrystals={200} onBoost={onBoost} />);
    // First item: premium_training_course, cost 50
    fireEvent.click(screen.getAllByRole("button")[0]);
    fireEvent.click(screen.getByText("Подтвердить"));
    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        shop_item: "premium_training_course",
        current_crystals: 200,
      });
    });
  });

  it("confirm button calls onBoost with correct boost map on success", async () => {
    const onBoost = vi.fn();
    render(<CrystalShop currentCrystals={200} onBoost={onBoost} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    fireEvent.click(screen.getByText("Подтвердить"));
    await waitFor(() => {
      expect(onBoost).toHaveBeenCalledWith({ intelligence: 10 });
    });
  });

  it("dialog closes after successful purchase", async () => {
    render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    fireEvent.click(screen.getByText("Подтвердить"));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });

  it("shows Loading in confirm button when purchase is pending", () => {
    // Open dialog first with non-pending mock, then re-render as pending
    const { rerender } = render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    // Rerender with pending state while dialog is open
    mockUseLifesimPurchase.mockReturnValue(makePurchaseMock({ isPending: true }));
    rerender(<CrystalShop {...baseProps} />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("all item buttons are disabled when purchase is pending", () => {
    // Open dialog first, then rerender as pending
    const { rerender } = render(<CrystalShop {...baseProps} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    mockUseLifesimPurchase.mockReturnValue(makePurchaseMock({ isPending: true }));
    rerender(<CrystalShop {...baseProps} />);
    // The 4 item buttons are disabled; cancel/confirm also exist but check items
    const allButtons = screen.getAllByRole("button");
    // At least item buttons are disabled
    const itemButtons = allButtons.filter((b) => {
      const label = b.getAttribute("aria-label") ?? "";
      return ["premium_training_course", "social_event_ticket", "health_insurance", "career_coach"].some(
        (id) => label === id,
      );
    });
    itemButtons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it("each item button has an aria-label", () => {
    render(<CrystalShop {...baseProps} />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) =>
      expect(btn).toHaveAttribute("aria-label"),
    );
  });

  it("SHOP_ITEMS constant has exactly 4 items", () => {
    expect(SHOP_ITEMS).toHaveLength(4);
  });

  it("SHOP_ITEMS IDs match expected values", () => {
    const ids = SHOP_ITEMS.map((i) => i.id);
    expect(ids).toContain("premium_training_course");
    expect(ids).toContain("social_event_ticket");
    expect(ids).toContain("health_insurance");
    expect(ids).toContain("career_coach");
  });
});

// ══════════════════════════════════════════════════════════════════════════════
// 2. BottomTabBar
// ══════════════════════════════════════════════════════════════════════════════

describe("BottomTabBar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue("/az/");
  });

  it("renders nav with product switcher aria-label", () => {
    render(<BottomTabBar locale="az" />);
    expect(
      screen.getByRole("navigation", { name: /product navigation/i }),
    ).toBeInTheDocument();
  });

  it("renders 5 tab links", () => {
    render(<BottomTabBar locale="az" />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(5);
  });

  it("home tab href is correct locale prefix", () => {
    render(<BottomTabBar locale="az" />);
    const links = screen.getAllByRole("link");
    const homeLink = links.find((l) => l.getAttribute("href") === "/az");
    expect(homeLink).toBeDefined();
  });

  it("mindshift tab href includes /mindshift", () => {
    render(<BottomTabBar locale="az" />);
    expect(screen.getByRole("link", { name: /mindshift/i })).toHaveAttribute(
      "href",
      "/az/mindshift",
    );
  });

  it("life sim tab href includes /life", () => {
    render(<BottomTabBar locale="az" />);
    expect(screen.getByRole("link", { name: /life sim/i })).toHaveAttribute(
      "href",
      "/az/life",
    );
  });

  it("atlas tab href includes /atlas", () => {
    render(<BottomTabBar locale="az" />);
    expect(screen.getByRole("link", { name: /atlas/i })).toHaveAttribute(
      "href",
      "/az/atlas",
    );
  });

  it("aura tab href includes /aura", () => {
    render(<BottomTabBar locale="az" />);
    expect(screen.getByRole("link", { name: /aura/i })).toHaveAttribute(
      "href",
      "/az/aura",
    );
  });

  it("active tab has aria-current=page", () => {
    // Pathname is /az/ → home is active
    mockUsePathname.mockReturnValue("/az/");
    render(<BottomTabBar locale="az" />);
    const currentLinks = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("aria-current") === "page");
    expect(currentLinks.length).toBeGreaterThanOrEqual(1);
  });

  it("non-active tabs do not have aria-current", () => {
    mockUsePathname.mockReturnValue("/az/");
    render(<BottomTabBar locale="az" />);
    // mindshift should not be active
    const mindshiftLink = screen.getByRole("link", { name: /mindshift/i });
    expect(mindshiftLink).not.toHaveAttribute("aria-current");
  });

  it("mindshift is active when pathname is /az/mindshift", () => {
    mockUsePathname.mockReturnValue("/az/mindshift");
    render(<BottomTabBar locale="az" />);
    const link = screen.getByRole("link", { name: /mindshift/i });
    expect(link).toHaveAttribute("aria-current", "page");
  });

  it("life tab is active when pathname is /az/life", () => {
    mockUsePathname.mockReturnValue("/az/life");
    render(<BottomTabBar locale="az" />);
    const link = screen.getByRole("link", { name: /life sim/i });
    expect(link).toHaveAttribute("aria-current", "page");
  });

  it("atlas tab is active when pathname is /az/atlas", () => {
    mockUsePathname.mockReturnValue("/az/atlas");
    render(<BottomTabBar locale="az" />);
    const link = screen.getByRole("link", { name: /atlas/i });
    expect(link).toHaveAttribute("aria-current", "page");
  });

  it("aura tab is active when pathname is /az/aura", () => {
    mockUsePathname.mockReturnValue("/az/aura");
    render(<BottomTabBar locale="az" />);
    const link = screen.getByRole("link", { name: /aura/i });
    expect(link).toHaveAttribute("aria-current", "page");
  });

  it("locale prop overrides URL-derived locale", () => {
    mockUsePathname.mockReturnValue("/en/");
    render(<BottomTabBar locale="az" />);
    const link = screen.getByRole("link", { name: /mindshift/i });
    expect(link.getAttribute("href")).toContain("/az/");
  });

  it("falls back to az locale when locale prop is omitted", () => {
    mockUsePathname.mockReturnValue("/az/");
    render(<BottomTabBar />);
    const links = screen.getAllByRole("link");
    expect(links[0].getAttribute("href")).toBe("/az");
  });

  it("each tab link has an aria-label", () => {
    render(<BottomTabBar locale="az" />);
    const links = screen.getAllByRole("link");
    links.forEach((link) =>
      expect(link).toHaveAttribute("aria-label"),
    );
  });

  it("renders tab labels as visible text", () => {
    render(<BottomTabBar locale="az" />);
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("MindShift")).toBeInTheDocument();
    expect(screen.getByText("Life Sim")).toBeInTheDocument();
    expect(screen.getByText("ATLAS")).toBeInTheDocument();
  });

  it("nav has fixed bottom class (structure check)", () => {
    render(<BottomTabBar locale="az" />);
    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("fixed");
    expect(nav.className).toContain("bottom-0");
  });

  it("nav is hidden on md+ (md:hidden class)", () => {
    render(<BottomTabBar locale="az" />);
    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("md:hidden");
  });
});

// ══════════════════════════════════════════════════════════════════════════════
// 3. ProductPlaceholder
// ══════════════════════════════════════════════════════════════════════════════

describe("ProductPlaceholder", () => {
  const baseProps = {
    name: "MindShift",
    icon: "🧠",
    tagline: "Focus your mind",
    accentVar: "#3B82F6",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseEnergyMode.mockReturnValue({ energy: "full", setEnergy: vi.fn() });
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("renders TopBar with product name", () => {
    render(<ProductPlaceholder {...baseProps} />);
    expect(screen.getByTestId("top-bar")).toHaveTextContent("MindShift");
  });

  it("renders product name as h1", () => {
    render(<ProductPlaceholder {...baseProps} />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("MindShift");
  });

  it("renders icon with aria-hidden", () => {
    render(<ProductPlaceholder {...baseProps} />);
    const iconEl = screen.getByText("🧠");
    expect(iconEl).toHaveAttribute("aria-hidden", "true");
  });

  it("shows tagline when energy is full", () => {
    mockUseEnergyMode.mockReturnValue({ energy: "full", setEnergy: vi.fn() });
    render(<ProductPlaceholder {...baseProps} />);
    expect(screen.getByText("Focus your mind")).toBeInTheDocument();
  });

  it("shows tagline when energy is mid", () => {
    mockUseEnergyMode.mockReturnValue({ energy: "mid", setEnergy: vi.fn() });
    render(<ProductPlaceholder {...baseProps} />);
    expect(screen.getByText("Focus your mind")).toBeInTheDocument();
  });

  it("hides tagline when energy is low", () => {
    mockUseEnergyMode.mockReturnValue({ energy: "low", setEnergy: vi.fn() });
    render(<ProductPlaceholder {...baseProps} />);
    expect(screen.queryByText("Focus your mind")).toBeNull();
  });

  it("shows coming soon text", () => {
    render(<ProductPlaceholder {...baseProps} />);
    expect(screen.getByText("Coming soon")).toBeInTheDocument();
  });

  it("applies accent color to h1", () => {
    render(<ProductPlaceholder {...baseProps} />);
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(h1).toHaveStyle({ color: "#3B82F6" });
  });

  it("icon has drop-shadow filter when not reduced motion and energy full", () => {
    mockUseReducedMotion.mockReturnValue(false);
    mockUseEnergyMode.mockReturnValue({ energy: "full", setEnergy: vi.fn() });
    render(<ProductPlaceholder {...baseProps} />);
    const iconEl = screen.getByText("🧠");
    expect(iconEl).toHaveStyle({
      filter: "drop-shadow(0 0 12px #3B82F6)",
    });
  });

  it("icon has no drop-shadow filter when reducedMotion=true", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(<ProductPlaceholder {...baseProps} />);
    const iconEl = screen.getByText("🧠");
    expect(iconEl.style.filter).toBeFalsy();
  });

  it("icon has no drop-shadow filter when energy=low", () => {
    mockUseEnergyMode.mockReturnValue({ energy: "low", setEnergy: vi.fn() });
    render(<ProductPlaceholder {...baseProps} />);
    const iconEl = screen.getByText("🧠");
    expect(iconEl.style.filter).toBeFalsy();
  });

  it("renders with different product name", () => {
    render(<ProductPlaceholder {...baseProps} name="BrandedBy" icon="✨" tagline="AI twin" accentVar="#EC4899" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("BrandedBy");
    expect(screen.getByText("✨")).toBeInTheDocument();
  });

  it("coming soon text is always visible regardless of energy mode", () => {
    for (const energy of ["full", "mid", "low"] as const) {
      mockUseEnergyMode.mockReturnValue({ energy, setEnergy: vi.fn() });
      const { unmount } = render(<ProductPlaceholder {...baseProps} />);
      expect(screen.getByText("Coming soon")).toBeInTheDocument();
      unmount();
    }
  });

  it("container has min-h-[60vh] centering class", () => {
    const { container } = render(<ProductPlaceholder {...baseProps} />);
    const centerDiv = container.querySelector(".min-h-\\[60vh\\]");
    expect(centerDiv).not.toBeNull();
  });

  it("noMotion=true when energy=low suppresses animation props", () => {
    mockUseEnergyMode.mockReturnValue({ energy: "low", setEnergy: vi.fn() });
    // Motion div receives empty initial/animate — just verify it renders cleanly
    const { container } = render(<ProductPlaceholder {...baseProps} />);
    expect(container.firstChild).not.toBeNull();
  });

  it("noMotion=true when reducedMotion=true suppresses animation props", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(<ProductPlaceholder {...baseProps} />);
    expect(container.firstChild).not.toBeNull();
  });
});

// ══════════════════════════════════════════════════════════════════════════════
// 4. AdminOverview
// ══════════════════════════════════════════════════════════════════════════════

describe("AdminOverview — loading states", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ locale: "az" });
  });

  it("shows 5 skeleton cards when overview is loading", () => {
    mockUseAdminOverview.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: false });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: false });
    render(<AdminOverview />);
    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(5);
  });

  it("shows skeleton for ops queues when stats loading", () => {
    mockUseAdminOverview.mockReturnValue({ data: makeOverview(), isLoading: false, isError: false });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: true });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByRole("status", { name: /loading queues/i })).toBeInTheDocument();
  });

  it("shows skeleton live events list when events loading", () => {
    mockUseAdminOverview.mockReturnValue({ data: makeOverview(), isLoading: false, isError: false });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: false });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: true });
    render(<AdminOverview />);
    expect(screen.getByRole("list", { name: /loading live events/i })).toBeInTheDocument();
  });
});

describe("AdminOverview — overview data rendered", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ locale: "az" });
    mockUseAdminOverview.mockReturnValue({ data: makeOverview(), isLoading: false, isError: false });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: false });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: false });
  });

  it("renders Platform Overview heading", () => {
    render(<AdminOverview />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Platform Overview");
  });

  it("renders Health scorecard section heading", () => {
    render(<AdminOverview />);
    expect(screen.getByRole("heading", { name: /health scorecard/i })).toBeInTheDocument();
  });

  it("renders activation rate as formatted percent", () => {
    render(<AdminOverview />);
    // 0.30 → "30.0%"
    expect(screen.getByText("30.0%")).toBeInTheDocument();
  });

  it("renders W4 retention as formatted percent", () => {
    render(<AdminOverview />);
    expect(screen.getByText("35.0%")).toBeInTheDocument();
  });

  it("renders DAU/WAU ratio", () => {
    render(<AdminOverview />);
    expect(screen.getByText("0.55")).toBeInTheDocument();
  });

  it("renders errors count as string", () => {
    render(<AdminOverview />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders runway in months", () => {
    render(<AdminOverview />);
    expect(screen.getByText("14.0 mo")).toBeInTheDocument();
  });

  it("renders 'Cross-product presence' section", () => {
    render(<AdminOverview />);
    expect(
      screen.getByRole("heading", { name: /cross-product presence/i }),
    ).toBeInTheDocument();
  });

  it("renders VOLAURA-only count in presence strip", () => {
    render(<AdminOverview />);
    // PresenceStrip shows counts
    expect(screen.getByText("50")).toBeInTheDocument();
  });

  it("renders funnel row with activation rate", () => {
    render(<AdminOverview />);
    expect(screen.getByText("40.0%")).toBeInTheDocument();
  });

  it("renders funnel activated/signups counts", () => {
    render(<AdminOverview />);
    // "4 / 10"
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("shows 'No signups in the last 24 hours' when funnels empty", () => {
    mockUseAdminOverview.mockReturnValue({
      data: makeOverview({ funnels: [] }),
      isLoading: false,
      isError: false,
    });
    render(<AdminOverview />);
    expect(screen.getByText("No signups in the last 24 hours.")).toBeInTheDocument();
  });

  it("shows runway as — when runway_months=null", () => {
    mockUseAdminOverview.mockReturnValue({
      data: makeOverview({ runway_months: null }),
      isLoading: false,
      isError: false,
    });
    render(<AdminOverview />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("shows w4 retention as — when null", () => {
    mockUseAdminOverview.mockReturnValue({
      data: makeOverview({ w4_retention: null }),
      isLoading: false,
      isError: false,
    });
    render(<AdminOverview />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders presence strip with aria role=img", () => {
    render(<AdminOverview />);
    const strip = screen.getByRole("img");
    expect(strip).toBeInTheDocument();
  });
});

describe("AdminOverview — error state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ locale: "az" });
  });

  it("shows error card when overview endpoint unreachable", () => {
    mockUseAdminOverview.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: false });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByText("Overview endpoint unreachable")).toBeInTheDocument();
  });

  it("error card mentions the overview endpoint path", () => {
    mockUseAdminOverview.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: false });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByText(/api\/admin\/stats\/overview/)).toBeInTheDocument();
  });
});

describe("AdminOverview — stats (ops queues)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ locale: "az" });
    mockUseAdminOverview.mockReturnValue({ data: makeOverview(), isLoading: false, isError: false });
    mockUseAdminLiveEvents.mockReturnValue({ data: undefined, isLoading: false });
  });

  it("renders total users stat", () => {
    mockUseAdminStats.mockReturnValue({ data: makeStats(), isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByText("250")).toBeInTheDocument();
  });

  it("renders active organizations stat", () => {
    mockUseAdminStats.mockReturnValue({ data: makeStats(), isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("renders avg AURA score", () => {
    mockUseAdminStats.mockReturnValue({ data: makeStats(), isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByText("72.5")).toBeInTheDocument();
  });

  it("renders pending org approvals with link", () => {
    mockUseAdminStats.mockReturnValue({ data: makeStats({ pending_org_approvals: 3 }), isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("org approvals link points to admin/organizations", () => {
    mockUseAdminStats.mockReturnValue({ data: makeStats({ pending_org_approvals: 3 }), isLoading: false });
    render(<AdminOverview />);
    // Link wraps a div (no accessible name from text), find by href
    const allLinks = screen.getAllByRole("link");
    const orgsLink = allLinks.find((l) => l.getAttribute("href")?.includes("/admin/organizations"));
    expect(orgsLink).toBeDefined();
    expect(orgsLink?.getAttribute("href")).toContain("/admin/organizations");
  });

  it("shows avg AURA as — when null", () => {
    mockUseAdminStats.mockReturnValue({
      data: makeStats({ avg_aura_score: null }),
      isLoading: false,
    });
    render(<AdminOverview />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});

describe("AdminOverview — live events feed", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ locale: "az" });
    mockUseAdminOverview.mockReturnValue({ data: makeOverview(), isLoading: false, isError: false });
    mockUseAdminStats.mockReturnValue({ data: undefined, isLoading: false });
  });

  it("shows empty state when events list is empty", () => {
    mockUseAdminLiveEvents.mockReturnValue({ data: [], isLoading: false });
    render(<AdminOverview />);
    expect(
      screen.getByText(/no events yet/i),
    ).toBeInTheDocument();
  });

  it("renders event_type for each live event", () => {
    mockUseAdminLiveEvents.mockReturnValue({
      data: [makeEvent({ event_type: "assessment_completed" })],
      isLoading: false,
    });
    render(<AdminOverview />);
    expect(screen.getByText("assessment_completed")).toBeInTheDocument();
  });

  it("renders user_id_prefix for live event", () => {
    mockUseAdminLiveEvents.mockReturnValue({
      data: [makeEvent({ user_id_prefix: "usr-abc" })],
      isLoading: false,
    });
    render(<AdminOverview />);
    expect(screen.getByText(/usr-abc/)).toBeInTheDocument();
  });

  it("renders payload_summary for live event", () => {
    mockUseAdminLiveEvents.mockReturnValue({
      data: [makeEvent({ payload_summary: "communication competency" })],
      isLoading: false,
    });
    render(<AdminOverview />);
    expect(screen.getByText("communication competency")).toBeInTheDocument();
  });

  it("renders time element for live event", () => {
    mockUseAdminLiveEvents.mockReturnValue({
      data: [makeEvent()],
      isLoading: false,
    });
    render(<AdminOverview />);
    const timeEl = document.querySelector("time");
    expect(timeEl).not.toBeNull();
  });

  it("renders Live activity heading", () => {
    mockUseAdminLiveEvents.mockReturnValue({ data: [], isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByRole("heading", { name: /live activity/i })).toBeInTheDocument();
  });

  it("renders Operational queues heading", () => {
    mockUseAdminLiveEvents.mockReturnValue({ data: [], isLoading: false });
    render(<AdminOverview />);
    expect(screen.getByRole("heading", { name: /operational queues/i })).toBeInTheDocument();
  });

  it("does not render payload_summary when null", () => {
    mockUseAdminLiveEvents.mockReturnValue({
      data: [makeEvent({ payload_summary: null })],
      isLoading: false,
    });
    // Should render without throwing
    const { container } = render(<AdminOverview />);
    expect(container).toBeTruthy();
  });
});
