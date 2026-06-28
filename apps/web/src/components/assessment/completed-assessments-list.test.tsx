import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import type { AnchorHTMLAttributes, HTMLAttributes, ReactNode } from "react";

const mockGetSession = vi.fn();

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { defaultValue?: string }) => opts?.defaultValue ?? key,
  }),
}));

vi.mock("lucide-react", () => ({
  History: () => null,
  ChevronRight: () => null,
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: (props: HTMLAttributes<HTMLDivElement>) => <div {...props} />,
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { children: ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import { CompletedAssessmentsList } from "./completed-assessments-list";

const FEED = {
  data: [
    {
      id: "sess-1",
      type: "assessment",
      created_at: "2026-06-09T10:00:00Z",
      metadata: { competency_slug: "communication" },
    },
    {
      id: "badge-1",
      type: "badge",
      created_at: "2026-06-08T10:00:00Z",
      metadata: {},
    },
    {
      id: "sess-2",
      type: "assessment",
      created_at: "2026-06-07T10:00:00Z",
      metadata: { competency_slug: "leadership" },
    },
  ],
};

describe("CompletedAssessmentsList (D-5)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "token-1" } },
    });
  });

  it("renders one row per completed assessment, deep-linked to its results page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => FEED,
      })
    );

    render(<CompletedAssessmentsList locale="en" />);

    await waitFor(() => {
      expect(screen.getByText("communication")).toBeInTheDocument();
    });
    expect(screen.getByText("leadership")).toBeInTheDocument();
    // badge item filtered out
    expect(screen.queryByText("badge-1")).not.toBeInTheDocument();

    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/en/assessment/sess-1/complete");
    expect(links[1]).toHaveAttribute("href", "/en/assessment/sess-2/complete");
  });

  it("renders nothing when there are no completed assessments", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      })
    );

    const { container } = render(<CompletedAssessmentsList locale="en" />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it("shows a muted non-blocking line when the feed fails to load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      })
    );

    render(<CompletedAssessmentsList locale="en" />);

    await waitFor(() => {
      expect(screen.getByText("Couldn't load past results right now.")).toBeInTheDocument();
    });
  });

  it("stays quiet when there is no auth session", async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const { container } = render(<CompletedAssessmentsList locale="en" />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
