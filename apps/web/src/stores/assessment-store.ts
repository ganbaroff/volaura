import { create } from "zustand";

export interface Question {
  id: string;
  text: string;
  type: "mcq" | "open_text" | "rating_scale";
  options?: string[];
  time_limit_seconds: number;
  difficulty_level: "easy" | "medium" | "hard";
}

interface AssessmentState {
  sessionId: string | null;
  currentQuestion: Question | null;
  selectedCompetencies: string[];
  currentCompetencyIndex: number;
  answeredCount: number;
  isSubmitting: boolean;
  isEvaluating: boolean; // 202 Accepted — waiting for LLM
  error: string | null;

  // Actions
  setSession: (id: string) => void;
  setQuestion: (q: Question | null) => void;
  setCompetencies: (c: string[]) => void;
  incrementAnswered: () => void;
  nextCompetency: () => void;
  setSubmitting: (v: boolean) => void;
  setEvaluating: (v: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
}

export const useAssessmentStore = create<AssessmentState>((set) => ({
  sessionId: null,
  currentQuestion: null,
  selectedCompetencies: [],
  currentCompetencyIndex: 0,
  answeredCount: 0,
  isSubmitting: false,
  isEvaluating: false,
  error: null,

  setSession: (id) => set({ sessionId: id }),
  setQuestion: (q) => set({ currentQuestion: q }),
  setCompetencies: (c) => set({ selectedCompetencies: c, currentCompetencyIndex: 0 }),
  incrementAnswered: () => set((s) => ({ answeredCount: s.answeredCount + 1 })),
  nextCompetency: () =>
    set((s) => ({
      currentCompetencyIndex: s.currentCompetencyIndex + 1,
      answeredCount: 0,
      sessionId: null,
      currentQuestion: null,
    })),
  setSubmitting: (v) => set({ isSubmitting: v }),
  setEvaluating: (v) => set({ isEvaluating: v }),
  setError: (e) => set({ error: e }),
  reset: () =>
    set({
      sessionId: null,
      currentQuestion: null,
      selectedCompetencies: [],
      currentCompetencyIndex: 0,
      answeredCount: 0,
      isSubmitting: false,
      isEvaluating: false,
      error: null,
    }),
}));
