/**
 * Shared mocks for Vitest tests.
 * Mock Next.js navigation, i18n, Supabase, and Framer Motion.
 */
import { vi } from "vitest";

// ── Next.js navigation mock ──
export const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
};

export const mockParams = { locale: "en" };

export const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
  useParams: () => mockParams,
  useSearchParams: () => mockSearchParams,
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
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { prefetch, ...htmlProps } = rest;
    return <a href={href} {...htmlProps}>{children}</a>;
  },
}));

// ── i18n mock — returns the key itself ──
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

// ── Framer Motion mock — render static divs ──
vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_target, prop: string) => {
        // Return a component that renders the element directly
        return ({
          children,
          ...rest
        }: {
          children?: React.ReactNode;
          [key: string]: unknown;
        }) => {
          // Filter out framer-motion specific props
          const htmlProps: Record<string, unknown> = {};
          for (const [key, value] of Object.entries(rest)) {
            if (
              !["initial", "animate", "exit", "transition", "variants", "whileHover", "whileTap", "whileInView", "layout"].includes(key)
            ) {
              htmlProps[key] = value;
            }
          }
          const Tag = prop as keyof React.JSX.IntrinsicElements;
          // @ts-ignore - dynamic tag element
          return <Tag {...htmlProps}>{children}</Tag>;
        };
      },
    }
  ),
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ── Supabase client mock ──
export const mockSupabaseAuth = {
  signInWithPassword: vi.fn(),
  signUp: vi.fn(),
  getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
  getUser: vi.fn().mockResolvedValue({ data: { user: null } }),
  onAuthStateChange: vi.fn(() => ({
    data: { subscription: { unsubscribe: vi.fn() } },
  })),
};

export const mockSupabase = {
  auth: mockSupabaseAuth,
  from: vi.fn(() => ({
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    single: vi.fn().mockResolvedValue({ data: null, error: null }),
    execute: vi.fn().mockResolvedValue({ data: [], error: null }),
  })),
};

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => mockSupabase,
}));
