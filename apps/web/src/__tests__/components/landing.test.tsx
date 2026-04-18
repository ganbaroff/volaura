import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import React from "react";

// ── Global browser API stubs ──────────────────────────────────────────────────

beforeAll(() => {
  // jsdom does not implement window.matchMedia
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

  // jsdom does not implement requestAnimationFrame
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb: FrameRequestCallback) =>
      setTimeout(cb, 16) as unknown as number;
    window.cancelAnimationFrame = (id: number) => clearTimeout(id);
  }
});

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { defaultValue?: string }) =>
      opts?.defaultValue ?? key,
    i18n: { language: "en" },
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/en",
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    className,
    "aria-label": ariaLabel,
    ...rest
  }: {
    href: string;
    children?: React.ReactNode;
    className?: string;
    "aria-label"?: string;
    [key: string]: unknown;
  }) =>
    React.createElement(
      "a",
      { href, className, "aria-label": ariaLabel, ...rest },
      children
    ),
}));

vi.mock("next/image", () => ({
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) =>
    React.createElement("img", props),
}));

vi.mock("framer-motion", () => {
  const makePassthrough =
    (tag: string) =>
    ({
      children,
      initial: _i,
      animate: _a,
      whileInView: _w,
      viewport: _vp,
      transition: _tr,
      variants: _v,
      className,
      style,
      "aria-label": ariaLabel,
      "aria-labelledby": ariaLabelledBy,
      ...rest
    }: {
      children?: React.ReactNode;
      initial?: unknown;
      animate?: unknown;
      whileInView?: unknown;
      viewport?: unknown;
      transition?: unknown;
      variants?: unknown;
      className?: string;
      style?: React.CSSProperties;
      "aria-label"?: string;
      "aria-labelledby"?: string;
      [key: string]: unknown;
    }) =>
      React.createElement(
        tag as keyof React.JSX.IntrinsicElements,
        { className, style, "aria-label": ariaLabel, "aria-labelledby": ariaLabelledBy, ...rest },
        children
      );

  return {
    motion: {
      div: makePassthrough("div"),
      h1: makePassthrough("h1"),
      h2: makePassthrough("h2"),
      p: makePassthrough("p"),
      article: makePassthrough("article"),
      section: makePassthrough("section"),
      span: makePassthrough("span"),
      ul: makePassthrough("ul"),
      li: makePassthrough("li"),
    },
    useReducedMotion: vi.fn(() => false),
    AnimatePresence: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
  };
});

vi.mock("@/hooks/queries/use-public-stats", () => ({
  usePublicStats: vi.fn(() => ({
    data: {
      total_professionals: 120,
      total_events: 30,
      total_assessments: 50,
      avg_aura_score: 72,
    },
    isError: false,
  })),
}));

vi.mock("@/i18nConfig", () => ({
  default: {
    locales: ["az", "en"],
    defaultLocale: "az",
    prefixDefault: true,
  },
}));

vi.mock("@/lib/utils/cn", () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(" "),
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { SocialProof } from "@/components/landing/social-proof";
import { OrgCta } from "@/components/landing/org-cta";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";
import { HowItWorks } from "@/components/landing/how-it-works";
import { FeaturesGrid } from "@/components/landing/features-grid";
import { HeroSection } from "@/components/landing/hero-section";
import { ImpactTicker } from "@/components/landing/impact-ticker";
import { SampleAuraPreview } from "@/components/landing/sample-aura-preview";
import { usePublicStats } from "@/hooks/queries/use-public-stats";
import { useReducedMotion } from "framer-motion";

// ── 1. SocialProof ────────────────────────────────────────────────────────────

describe("SocialProof — rendering", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => {})) // never resolves → count stays null
    );
  });

  it("renders a section element", async () => {
    await act(async () => { render(<SocialProof />); });
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("has aria-label on section", async () => {
    await act(async () => { render(<SocialProof />); });
    const section = document.querySelector("section");
    expect(section).toHaveAttribute("aria-label");
  });

  it("shows generic count text initially (count null before fetch resolves)", async () => {
    await act(async () => { render(<SocialProof />); });
    expect(
      screen.getByText("Join professionals already proving their skills")
    ).toBeInTheDocument();
  });

  it("shows founder text", async () => {
    await act(async () => { render(<SocialProof />); });
    expect(
      screen.getByText(
        "Founded by Yusif Ganbarov. One person, one vision: verified competency as the global standard for professional identity."
      )
    ).toBeInTheDocument();
  });

  it("shows subtitle text", async () => {
    await act(async () => { render(<SocialProof />); });
    expect(screen.getByText("Built in Baku. For the world.")).toBeInTheDocument();
  });

  it("shows count text after fetch resolves with data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          json: () => Promise.resolve({ total_professionals: 42 }),
        })
      )
    );
    await act(async () => { render(<SocialProof />); });
    // t returns defaultValue: "Join ${count} professionals already proving their skills"
    await waitFor(() => {
      expect(
        screen.getByText("Join 42 professionals already proving their skills")
      ).toBeInTheDocument();
    });
  });

  it("stays on generic text when fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("network error")))
    );
    await act(async () => { render(<SocialProof />); });
    await waitFor(() => {
      expect(
        screen.getByText("Join professionals already proving their skills")
      ).toBeInTheDocument();
    });
  });

  it("stays on generic text when API returns null total_professionals", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          json: () => Promise.resolve({ total_professionals: null }),
        })
      )
    );
    await act(async () => { render(<SocialProof />); });
    await waitFor(() => {
      expect(
        screen.getByText("Join professionals already proving their skills")
      ).toBeInTheDocument();
    });
  });
});

// ── 2. OrgCta ─────────────────────────────────────────────────────────────────

describe("OrgCta — rendering", () => {
  it("renders a section element", () => {
    render(<OrgCta locale="en" />);
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("renders heading text (h2)", () => {
    render(<OrgCta locale="en" />);
    expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
  });

  it("renders org title key", () => {
    render(<OrgCta locale="en" />);
    expect(screen.getByText("landing.orgTitle")).toBeInTheDocument();
  });

  it("renders subtitle key", () => {
    render(<OrgCta locale="en" />);
    expect(screen.getByText("landing.orgSubtitle")).toBeInTheDocument();
  });

  it("renders CTA link with correct locale href", () => {
    render(<OrgCta locale="en" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/en/signup");
  });

  it("CTA link contains cta text", () => {
    render(<OrgCta locale="en" />);
    expect(screen.getByText("landing.orgCta")).toBeInTheDocument();
  });

  it("uses az locale in href when locale=az", () => {
    render(<OrgCta locale="az" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/az/signup");
  });
});

// ── 3. LandingFooter ─────────────────────────────────────────────────────────

describe("LandingFooter — rendering", () => {
  it("renders a footer element", () => {
    render(<LandingFooter locale="en" />);
    expect(document.querySelector("footer")).toBeInTheDocument();
  });

  it("shows Volaura brand name", () => {
    render(<LandingFooter locale="en" />);
    expect(screen.getAllByText("Volaura").length).toBeGreaterThan(0);
  });

  it("shows tagline key", () => {
    render(<LandingFooter locale="en" />);
    expect(screen.getByText("landing.footerTagline")).toBeInTheDocument();
  });

  it("shows rights key", () => {
    render(<LandingFooter locale="en" />);
    expect(screen.getByText(/landing\.footerRights/)).toBeInTheDocument();
  });

  it("renders nav with aria-label Footer navigation", () => {
    render(<LandingFooter locale="en" />);
    expect(
      screen.getByRole("navigation", { name: "Footer navigation" })
    ).toBeInTheDocument();
  });

  it("events link points to locale path", () => {
    render(<LandingFooter locale="en" />);
    const eventsLink = screen.getByRole("link", { name: "nav.events" });
    expect(eventsLink).toHaveAttribute("href", "/en/events");
  });

  it("signup link points to locale path", () => {
    render(<LandingFooter locale="en" />);
    const link = screen.getByRole("link", { name: "auth.signup" });
    expect(link).toHaveAttribute("href", "/en/signup");
  });

  it("login link points to locale path", () => {
    render(<LandingFooter locale="en" />);
    const link = screen.getByRole("link", { name: "auth.login" });
    expect(link).toHaveAttribute("href", "/en/login");
  });

  it("displays current year in copyright", () => {
    render(<LandingFooter locale="en" />);
    const year = new Date().getFullYear().toString();
    expect(screen.getByText(new RegExp(year))).toBeInTheDocument();
  });

  it("uses az locale in hrefs when locale=az", () => {
    render(<LandingFooter locale="az" />);
    const eventsLink = screen.getByRole("link", { name: "nav.events" });
    expect(eventsLink).toHaveAttribute("href", "/az/events");
  });
});

// ── 4. LandingNav ────────────────────────────────────────────────────────────

describe("LandingNav — rendering", () => {
  it("renders a header element", () => {
    render(<LandingNav locale="en" />);
    expect(document.querySelector("header")).toBeInTheDocument();
  });

  it("renders logo link with Volaura home aria-label", () => {
    render(<LandingNav locale="en" />);
    expect(screen.getByRole("link", { name: "Volaura home" })).toBeInTheDocument();
  });

  it("logo link points to locale root", () => {
    render(<LandingNav locale="en" />);
    expect(screen.getByRole("link", { name: "Volaura home" })).toHaveAttribute("href", "/en");
  });

  it("renders main navigation with aria-label", () => {
    render(<LandingNav locale="en" />);
    expect(
      screen.getByRole("navigation", { name: "Main navigation" })
    ).toBeInTheDocument();
  });

  it("nav contains events link", () => {
    render(<LandingNav locale="en" />);
    const eventsLink = screen.getByRole("link", { name: "nav.events" });
    expect(eventsLink).toHaveAttribute("href", "/en/events");
  });

  it("renders login link", () => {
    render(<LandingNav locale="en" />);
    expect(screen.getByRole("link", { name: "auth.login" })).toHaveAttribute("href", "/en/login");
  });

  it("renders signup link", () => {
    render(<LandingNav locale="en" />);
    expect(screen.getByRole("link", { name: "auth.signup" })).toHaveAttribute("href", "/en/signup");
  });

  it("signup link has primary bg class", () => {
    render(<LandingNav locale="en" />);
    const signupLink = screen.getByRole("link", { name: "auth.signup" });
    expect(signupLink.className).toContain("bg-primary");
  });

  it("uses az locale in hrefs when locale=az", () => {
    render(<LandingNav locale="az" />);
    expect(screen.getByRole("link", { name: "Volaura home" })).toHaveAttribute("href", "/az");
  });

  it("renders LanguageSwitcher buttons", () => {
    render(<LandingNav locale="en" />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });
});

// ── 5. HowItWorks ────────────────────────────────────────────────────────────

describe("HowItWorks — rendering", () => {
  it("renders a section element", () => {
    render(<HowItWorks />);
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("renders main heading (h2)", () => {
    render(<HowItWorks />);
    expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
  });

  it("renders how-it-works title key", () => {
    render(<HowItWorks />);
    expect(screen.getByText("landing.howItWorksTitle")).toBeInTheDocument();
  });

  it("renders subtitle key", () => {
    render(<HowItWorks />);
    expect(screen.getByText("landing.howItWorksSubtitle")).toBeInTheDocument();
  });

  it("renders all 3 step headings", () => {
    render(<HowItWorks />);
    expect(screen.getByText("landing.step1Title")).toBeInTheDocument();
    expect(screen.getByText("landing.step2Title")).toBeInTheDocument();
    expect(screen.getByText("landing.step3Title")).toBeInTheDocument();
  });

  it("renders all 3 step descriptions", () => {
    render(<HowItWorks />);
    expect(screen.getByText("landing.step1Desc")).toBeInTheDocument();
    expect(screen.getByText("landing.step2Desc")).toBeInTheDocument();
    expect(screen.getByText("landing.step3Desc")).toBeInTheDocument();
  });

  it("renders step numbers 1, 2, 3", () => {
    render(<HowItWorks />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("decorative elements have aria-hidden", () => {
    const { container } = render(<HowItWorks />);
    const hidden = container.querySelectorAll('[aria-hidden="true"]');
    expect(hidden.length).toBeGreaterThan(0);
  });

  it("renders step icons with aria-hidden", () => {
    const { container } = render(<HowItWorks />);
    const iconSvgs = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(iconSvgs.length).toBeGreaterThan(0);
  });
});

// ── 6. FeaturesGrid ──────────────────────────────────────────────────────────

describe("FeaturesGrid — rendering", () => {
  it("renders a section element", () => {
    render(<FeaturesGrid />);
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("renders main heading (h2)", () => {
    render(<FeaturesGrid />);
    expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
  });

  it("renders features title key", () => {
    render(<FeaturesGrid />);
    expect(screen.getByText("landing.featuresTitle")).toBeInTheDocument();
  });

  it("renders features subtitle key", () => {
    render(<FeaturesGrid />);
    expect(screen.getByText("landing.featuresSubtitle")).toBeInTheDocument();
  });

  it("renders exactly 3 feature card headings", () => {
    render(<FeaturesGrid />);
    expect(screen.getByText("landing.feature1Title")).toBeInTheDocument();
    expect(screen.getByText("landing.feature2Title")).toBeInTheDocument();
    expect(screen.getByText("landing.feature3Title")).toBeInTheDocument();
  });

  it("renders exactly 3 feature descriptions", () => {
    render(<FeaturesGrid />);
    expect(screen.getByText("landing.feature1Desc")).toBeInTheDocument();
    expect(screen.getByText("landing.feature2Desc")).toBeInTheDocument();
    expect(screen.getByText("landing.feature3Desc")).toBeInTheDocument();
  });

  it("renders 3 card icons with aria-hidden", () => {
    const { container } = render(<FeaturesGrid />);
    const icons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(icons.length).toBe(3);
  });

  it("no CTA link inside cards (Law 5 — one CTA per screen)", () => {
    render(<FeaturesGrid />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});

// ── 7. HeroSection ───────────────────────────────────────────────────────────

describe("HeroSection — rendering", () => {
  it("renders a section element", () => {
    render(<HeroSection locale="en" />);
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("renders h1 heading", () => {
    render(<HeroSection locale="en" />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders hero title key", () => {
    render(<HeroSection locale="en" />);
    expect(screen.getByText("landing.heroTitle")).toBeInTheDocument();
  });

  it("renders hero subtitle key", () => {
    render(<HeroSection locale="en" />);
    expect(screen.getByText("landing.heroSubtitle")).toBeInTheDocument();
  });

  it("renders primary CTA link with locale href", () => {
    render(<HeroSection locale="en" />);
    const cta = screen.getByRole("link", { name: "landing.heroCta" });
    expect(cta).toHaveAttribute("href", "/en/signup");
  });

  it("renders org CTA link with type=organization href", () => {
    render(<HeroSection locale="en" />);
    const orgCta = screen.getByRole("link", { name: "landing.heroCtaOrg" });
    expect(orgCta).toHaveAttribute("href", "/en/signup?type=organization");
  });

  it("renders all 3 badge pill tiers", () => {
    render(<HeroSection locale="en" />);
    expect(screen.getByText(/aura\.platinum/)).toBeInTheDocument();
    expect(screen.getByText(/aura\.gold/)).toBeInTheDocument();
    expect(screen.getByText(/aura\.silver/)).toBeInTheDocument();
  });

  it("badge pills show scores", () => {
    render(<HeroSection locale="en" />);
    expect(screen.getByText(/94\/100/)).toBeInTheDocument();
    expect(screen.getByText(/81\/100/)).toBeInTheDocument();
    expect(screen.getByText(/67\/100/)).toBeInTheDocument();
  });

  it("background gradient has aria-hidden", () => {
    const { container } = render(<HeroSection locale="en" />);
    const hidden = container.querySelector('[aria-hidden="true"]');
    expect(hidden).toBeInTheDocument();
  });

  it("uses az locale in CTA hrefs when locale=az", () => {
    render(<HeroSection locale="az" />);
    const cta = screen.getByRole("link", { name: "landing.heroCta" });
    expect(cta).toHaveAttribute("href", "/az/signup");
  });

  it("primary CTA has btn-primary-gradient class", () => {
    render(<HeroSection locale="en" />);
    const cta = screen.getByRole("link", { name: "landing.heroCta" });
    expect(cta.className).toContain("btn-primary-gradient");
  });
});

describe("HeroSection — reduced motion", () => {
  it("renders content when useReducedMotion is true", () => {
    vi.mocked(useReducedMotion).mockReturnValueOnce(true);
    render(<HeroSection locale="en" />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });
});

// ── 8. ImpactTicker ──────────────────────────────────────────────────────────

describe("ImpactTicker — rendering (data available)", () => {
  it("renders a section element", () => {
    render(<ImpactTicker />);
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("has aria-label Platform impact statistics", () => {
    render(<ImpactTicker />);
    expect(
      screen.getByRole("region", { name: "Platform impact statistics" })
    ).toBeInTheDocument();
  });

  it("renders professionals label key", () => {
    render(<ImpactTicker />);
    expect(screen.getByText("landing.impactProfessionals")).toBeInTheDocument();
  });

  it("renders events label key", () => {
    render(<ImpactTicker />);
    expect(screen.getByText("landing.impactEvents")).toBeInTheDocument();
  });

  it("renders hours label key", () => {
    render(<ImpactTicker />);
    expect(screen.getByText("landing.impactHours")).toBeInTheDocument();
  });

  it("renders 3 stat card containers", () => {
    const { container } = render(<ImpactTicker />);
    const cards = container.querySelectorAll(".rounded-2xl");
    expect(cards.length).toBe(3);
  });

  it("renders stat card icons with aria-hidden", () => {
    const { container } = render(<ImpactTicker />);
    const icons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(icons.length).toBeGreaterThanOrEqual(3);
  });
});

describe("ImpactTicker — below threshold fallback (value < 5)", () => {
  it("shows professionals fallback label when total_professionals is 0", () => {
    vi.mocked(usePublicStats).mockReturnValueOnce({
      data: {
        total_professionals: 0,
        total_events: 0,
        total_assessments: 0,
        avg_aura_score: 0,
      },
      isError: false,
    } as ReturnType<typeof usePublicStats>);
    render(<ImpactTicker />);
    expect(
      screen.getByText("landing.statsFallback.professionals")
    ).toBeInTheDocument();
  });

  it("shows events fallback label when total_events is 0", () => {
    vi.mocked(usePublicStats).mockReturnValueOnce({
      data: {
        total_professionals: 0,
        total_events: 0,
        total_assessments: 0,
        avg_aura_score: 0,
      },
      isError: false,
    } as ReturnType<typeof usePublicStats>);
    render(<ImpactTicker />);
    expect(
      screen.getByText("landing.statsFallback.events")
    ).toBeInTheDocument();
  });

  it("shows number when value >= 5 (no fallback)", () => {
    vi.mocked(usePublicStats).mockReturnValueOnce({
      data: {
        total_professionals: 120,
        total_events: 30,
        total_assessments: 50,
        avg_aura_score: 72,
      },
      isError: false,
    } as ReturnType<typeof usePublicStats>);
    render(<ImpactTicker />);
    // professionals count 120 >= 5, label (not fallback) shown
    expect(screen.getByText("landing.impactProfessionals")).toBeInTheDocument();
  });
});

describe("ImpactTicker — error state", () => {
  it("shows fallback stats on API error (values = 0, below threshold)", () => {
    vi.mocked(usePublicStats).mockReturnValueOnce({
      data: undefined,
      isError: true,
    } as ReturnType<typeof usePublicStats>);
    render(<ImpactTicker />);
    // With error, FALLBACK_STATS all = 0, belowThreshold fires for professionals + events
    expect(
      screen.getByText("landing.statsFallback.professionals")
    ).toBeInTheDocument();
  });
});

// ── 9. SampleAuraPreview ─────────────────────────────────────────────────────

describe("SampleAuraPreview — rendering", () => {
  it("renders a section element", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(document.querySelector("section")).toBeInTheDocument();
  });

  it("section is aria-labelledby sample-aura-heading", () => {
    const { container } = render(<SampleAuraPreview locale="en" />);
    const section = container.querySelector("section");
    expect(section).toHaveAttribute("aria-labelledby", "sample-aura-heading");
  });

  it("heading has id sample-aura-heading", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(document.getElementById("sample-aura-heading")).toBeInTheDocument();
  });

  it("renders preview title (defaultValue)", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(
      screen.getByText("What your profile could look like")
    ).toBeInTheDocument();
  });

  it("renders preview subtitle (defaultValue)", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(
      screen.getByText("Sample profile — no account required to preview")
    ).toBeInTheDocument();
  });

  it("renders sample badge label", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("Sample profile")).toBeInTheDocument();
  });

  it("renders fictional label", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("Fictional example")).toBeInTheDocument();
  });

  it("renders Leyla Mammadova name", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("Leyla Mammadova")).toBeInTheDocument();
  });

  it("renders primary score 74", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("74")).toBeInTheDocument();
  });

  it("renders /100 label for primary score", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("/ 100")).toBeInTheDocument();
  });

  it("renders all 4 competency labels", () => {
    render(<SampleAuraPreview locale="en" />);
    // t(labelKey, { defaultValue: slug }) → returns slug (the defaultValue)
    expect(screen.getByText("communication")).toBeInTheDocument();
    expect(screen.getByText("reliability")).toBeInTheDocument();
    expect(screen.getByText("english_proficiency")).toBeInTheDocument();
    expect(screen.getByText("leadership")).toBeInTheDocument();
  });

  it("renders other competency scores as numbers", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("68")).toBeInTheDocument();
    expect(screen.getByText("71")).toBeInTheDocument();
    expect(screen.getByText("62")).toBeInTheDocument();
  });

  it("renders silver tier badge text", () => {
    render(<SampleAuraPreview locale="en" />);
    // t("aura.silver", { defaultValue: "silver" }) → returns "silver"
    expect(screen.getByText("silver")).toBeInTheDocument();
  });

  it("renders badge tier label", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(screen.getByText("Badge tier")).toBeInTheDocument();
  });

  it("renders sample cta prompt", () => {
    render(<SampleAuraPreview locale="en" />);
    expect(
      screen.getByText("Take the assessment and earn your own verified profile.")
    ).toBeInTheDocument();
  });

  it("renders signup CTA link with locale", () => {
    render(<SampleAuraPreview locale="en" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/en/signup");
  });

  it("uses az locale in CTA href when locale=az", () => {
    render(<SampleAuraPreview locale="az" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/az/signup");
  });

  it("article has aria-label for profile preview", () => {
    const { container } = render(<SampleAuraPreview locale="en" />);
    const article = container.querySelector("article");
    expect(article).toHaveAttribute("aria-label", "Sample AURA profile preview");
  });

  it("renders 3 progress bars for other competencies", () => {
    const { container } = render(<SampleAuraPreview locale="en" />);
    const bars = container.querySelectorAll<HTMLElement>('[style*="width"]');
    expect(bars.length).toBe(3);
  });

  it("progress bar widths match other competency scores", () => {
    const { container } = render(<SampleAuraPreview locale="en" />);
    const bars = Array.from(container.querySelectorAll<HTMLElement>('[style*="width"]'));
    const widths = bars.map((b) => b.style.width);
    expect(widths).toContain("68%");
    expect(widths).toContain("71%");
    expect(widths).toContain("62%");
  });

  it("shield icon in sample badge has aria-hidden", () => {
    const { container } = render(<SampleAuraPreview locale="en" />);
    const icons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(icons.length).toBeGreaterThan(0);
  });

  it("badge tier circle is aria-hidden", () => {
    const { container } = render(<SampleAuraPreview locale="en" />);
    const hiddenDivs = container.querySelectorAll('[aria-hidden="true"]');
    expect(hiddenDivs.length).toBeGreaterThan(0);
  });
});
