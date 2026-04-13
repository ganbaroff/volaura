import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// Mock next/navigation with usePathname
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
  usePathname: () => "/en/dashboard",
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: unknown }) => {
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
  motion: new Proxy({}, {
    get: (_target, prop: string) => {
      return ({ children, ...rest }: { children?: React.ReactNode; [key: string]: unknown }) => {
        const htmlProps: Record<string, unknown> = {};
        for (const [key, value] of Object.entries(rest)) {
          if (!["initial", "animate", "exit", "transition", "variants", "whileHover", "whileTap", "whileInView", "layout"].includes(key)) {
            htmlProps[key] = value;
          }
        }
        const Component = prop as React.ElementType;
        return <Component {...htmlProps}>{children}</Component>;
      };
    },
  }),
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock auth store
vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ clear: vi.fn(), user: null, token: null }),
}));

// Mock Supabase client (needed for handleLogout)
vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: { signOut: vi.fn().mockResolvedValue({}) },
  }),
}));

// Mock TanStack Query hooks used by Sidebar
vi.mock("@/hooks/queries/use-notifications", () => ({
  useUnreadCount: () => ({ data: { unread_count: 0 } }),
}));

vi.mock("@/hooks/queries/use-profile", () => ({
  useProfile: () => ({ data: null }),
}));

import { Sidebar } from "./sidebar";

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("Sidebar", () => {
  it("renders at least one navigation element", () => {
    renderWithQueryClient(<Sidebar />);
    const navs = screen.getAllByRole("navigation");
    expect(navs.length).toBeGreaterThan(0);
  });

  it("renders navigation links", () => {
    renderWithQueryClient(<Sidebar />);
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThan(0);
  });

  it("has aria-label on at least one navigation element", () => {
    renderWithQueryClient(<Sidebar />);
    const navs = screen.getAllByRole("navigation");
    const withLabel = navs.filter(nav => nav.hasAttribute("aria-label"));
    expect(withLabel.length).toBeGreaterThan(0);
  });
});
