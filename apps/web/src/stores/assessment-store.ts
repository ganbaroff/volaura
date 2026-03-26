import { create } from "zustand";

/**
 * Matches backend QuestionOut schema (apps/api/app/schemas/assessment.py)
 * Fields: id, question_type, question_en, question_az, options, competency_id
 */
export interface Question {
  id: string;
  question_type: string; // "mcq" | "open_ended" | "sjt"
  question_en: string;
  question_az: string;
  options: Array<{ key: string; text_en: string; text_az: string }> | null;
  competency_id: string;
}

/**
 * Matches backend SessionOut schema
 */
export interface SessionState {
  session_id: string;
  competency_slug: string;
  role_level: string;
  questions_answered: number;
  is_complete: boolean;
  stop_reason: string | null;
  next_question: Question | null;
}

/**
 * Matches backend AnswerFeedback schema
 */
export interface AnswerFeedback {
  session_id: string;
  question_id: string;
  timing_warning: string | null;
  session: SessionState;
}

interface AssessmentStore {
  sessionId: string | null;
  currentQuestion: Question | null;
  selectedCompetencies: string[];
  currentCompetencyIndex: number;
  answeredCount: number;
  isSubmitting: boolean;
  error: string | null;

  // Actions
  setSession: (id: string) => void;
  setQuestion: (q: Question | null) => void;
  setCompetencies: (c: string[]) => void;
  incrementAnswered: () => void;
  nextCompetency: () => void;
  setSubmitting: (v: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
}

export const useAssessmentStore = create<AssessmentStore>((set) => ({
  sessionId: null,
  currentQuestion: null,
  selectedCompetencies: [],
  currentCompetencyIndex: 0,
  answeredCount: 0,
  isSubmitting: false,
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
  setError: (e) => set({ error: e }),
  reset: () =>
    set({
      sessionId: null,
      currentQuestion: null,
      selectedCompetencies: [],
      currentCompetencyIndex: 0,
      answeredCount: 0,
      isSubmitting: false,
      error: null,
    }),
}));
