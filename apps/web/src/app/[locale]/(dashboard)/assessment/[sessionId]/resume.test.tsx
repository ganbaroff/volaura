import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

const mockReplace = vi.fn();
const mockPush = vi.fn();
const mockRestoreProgress = vi.fn();
const mockReset = vi.fn();
const mockGetSession = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useParams: () => ({ locale: "en", sessionId: "session-123" }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { defaultValue?: string }) => opts?.defaultValue ?? key,
    i18n: { language: "en" },
  }),
}));

vi.mock("framer-motion", () => ({
  AnimatePresence: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("lucide-react", () => ({
  AlertCircle: () => null,
  Loader2: () => null,
  ChevronLeft: () => null,
  RefreshCw: () => null,
}));

vi.mock("@/hooks/use-focus-trap", () => ({
  useFocusTrap: () => ({ current: null }),
}));

vi.mock("@/hooks/use-analytics", () => ({
  useTrackEvent: () => vi.fn(),
}));

vi.mock("@/hooks/use-energy-mode", () => ({
  useEnergyMode: () => ({ energy: "full" }),
}));

vi.mock("@/components/assessment/question-card", () => ({
  QuestionCard: () => null,
}));

vi.mock("@/components/assessment/progress-bar", () => ({
  ProgressBar: () => null,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    ...props
  }: ButtonHTMLAttributes<HTMLButtonElement>) => <button {...props}>{children}</button>,
}));

vi.mock("@/components/ui/alert", () => ({
  Alert: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
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

vi.mock("@/stores/assessment-store", () => ({
  useAssessmentStore: () => ({
    currentQuestion: null,
    selectedCompetencies: [],
    currentCompetencyIndex: 0,
    answeredCount: 0,
    isSubmitting: false,
    _hydrated: true,
    setQuestion: vi.fn(),
    setSession: vi.fn(),
    setCompetencies: vi.fn(),
    restoreProgress: mockRestoreProgress,
    setSubmitting: vi.fn(),
    incrementAnswered: vi.fn(),
    nextCompetency: vi.fn(),
    reset: mockReset,
  }),
}));

import QuestionPage from "./page";

describe("QuestionPage resume flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "token-123" } },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          session_id: "session-123",
          competency_slug: "communication",
          status: "in_progress",
          questions_answered: 2,
          next_question: {
            id: "question-1",
            question_type: "mcq",
            question_en: "What would you do?",
            question_az: "Nə edərdiniz?",
            options: [{ key: "a", text_en: "One", text_az: "Bir" }],
            competency_id: "comp-1",
          },
          assessment_plan_competencies: ["communication", "leadership"],
          assessment_plan_current_index: 0,
          is_resumable: true,
        }),
      }),
    );
  });

  it("uses the single /api assessment session path when resuming", async () => {
    render(<QuestionPage />);

    fireEvent.click(screen.getByRole("button", { name: "Resume session" }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/api/assessment/session/session-123", {
        headers: { Authorization: "Bearer token-123" },
      });
    });

    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/api/assessment/session/"),
      expect.anything(),
    );
    expect(mockRestoreProgress).toHaveBeenCalledWith({
      sessionId: "session-123",
      question: {
        id: "question-1",
        question_type: "mcq",
        question_en: "What would you do?",
        question_az: "Nə edərdiniz?",
        options: [{ key: "a", text_en: "One", text_az: "Bir" }],
        competency_id: "comp-1",
      },
      competencies: ["communication", "leadership"],
      currentCompetencyIndex: 0,
      answeredCount: 2,
    });
  });
});
