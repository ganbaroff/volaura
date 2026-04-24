import { describe, it, expect, beforeEach } from "vitest";
import { useAssessmentStore } from "./assessment-store";

const sampleQuestion = {
  id: "q-1",
  question_type: "mcq",
  question_en: "What is leadership?",
  question_az: "Liderlik nədir?",
  options: [
    { key: "a", text_en: "Option A", text_az: "Variant A" },
    { key: "b", text_en: "Option B", text_az: "Variant B" },
  ],
  competency_id: "comp-1",
};

describe("assessment-store", () => {
  beforeEach(() => {
    useAssessmentStore.getState().reset();
  });

  it("starts with null session and zero counts", () => {
    const state = useAssessmentStore.getState();
    expect(state.sessionId).toBeNull();
    expect(state.currentQuestion).toBeNull();
    expect(state.selectedCompetencies).toEqual([]);
    expect(state.currentCompetencyIndex).toBe(0);
    expect(state.answeredCount).toBe(0);
    expect(state.isSubmitting).toBe(false);
    expect(state.error).toBeNull();
  });

  it("setSession stores session id", () => {
    useAssessmentStore.getState().setSession("sess-abc");
    expect(useAssessmentStore.getState().sessionId).toBe("sess-abc");
  });

  it("setQuestion stores question object", () => {
    useAssessmentStore.getState().setQuestion(sampleQuestion);
    expect(useAssessmentStore.getState().currentQuestion).toEqual(sampleQuestion);
  });

  it("setQuestion accepts null", () => {
    useAssessmentStore.getState().setQuestion(sampleQuestion);
    useAssessmentStore.getState().setQuestion(null);
    expect(useAssessmentStore.getState().currentQuestion).toBeNull();
  });

  it("setCompetencies stores list and resets index to 0", () => {
    useAssessmentStore.getState().setCompetencies(["comm", "lead", "tech"]);
    const state = useAssessmentStore.getState();
    expect(state.selectedCompetencies).toEqual(["comm", "lead", "tech"]);
    expect(state.currentCompetencyIndex).toBe(0);
  });

  it("setCompetencies resets index even if previously advanced", () => {
    useAssessmentStore.getState().setCompetencies(["a", "b"]);
    useAssessmentStore.getState().nextCompetency();
    expect(useAssessmentStore.getState().currentCompetencyIndex).toBe(1);
    useAssessmentStore.getState().setCompetencies(["x", "y", "z"]);
    expect(useAssessmentStore.getState().currentCompetencyIndex).toBe(0);
  });

  it("restoreProgress rehydrates the full plan, index, answer count, session, and question", () => {
    useAssessmentStore.getState().restoreProgress({
      sessionId: "sess-restore",
      question: sampleQuestion,
      competencies: ["communication", "leadership", "tech_literacy"],
      currentCompetencyIndex: 1,
      answeredCount: 4,
    });

    const state = useAssessmentStore.getState();
    expect(state.sessionId).toBe("sess-restore");
    expect(state.currentQuestion).toEqual(sampleQuestion);
    expect(state.selectedCompetencies).toEqual(["communication", "leadership", "tech_literacy"]);
    expect(state.currentCompetencyIndex).toBe(1);
    expect(state.answeredCount).toBe(4);
  });

  it("incrementAnswered bumps count by 1", () => {
    useAssessmentStore.getState().incrementAnswered();
    useAssessmentStore.getState().incrementAnswered();
    useAssessmentStore.getState().incrementAnswered();
    expect(useAssessmentStore.getState().answeredCount).toBe(3);
  });

  it("nextCompetency advances index and resets session state", () => {
    useAssessmentStore.getState().setSession("sess-1");
    useAssessmentStore.getState().setQuestion(sampleQuestion);
    useAssessmentStore.getState().incrementAnswered();
    useAssessmentStore.getState().incrementAnswered();

    useAssessmentStore.getState().nextCompetency();

    const state = useAssessmentStore.getState();
    expect(state.currentCompetencyIndex).toBe(1);
    expect(state.answeredCount).toBe(0);
    expect(state.sessionId).toBeNull();
    expect(state.currentQuestion).toBeNull();
  });

  it("nextCompetency can advance multiple times", () => {
    useAssessmentStore.getState().setCompetencies(["a", "b", "c", "d"]);
    useAssessmentStore.getState().nextCompetency();
    useAssessmentStore.getState().nextCompetency();
    useAssessmentStore.getState().nextCompetency();
    expect(useAssessmentStore.getState().currentCompetencyIndex).toBe(3);
  });

  it("setSubmitting toggles submitting flag", () => {
    useAssessmentStore.getState().setSubmitting(true);
    expect(useAssessmentStore.getState().isSubmitting).toBe(true);
    useAssessmentStore.getState().setSubmitting(false);
    expect(useAssessmentStore.getState().isSubmitting).toBe(false);
  });

  it("setError stores error message", () => {
    useAssessmentStore.getState().setError("Network failed");
    expect(useAssessmentStore.getState().error).toBe("Network failed");
  });

  it("setError clears with null", () => {
    useAssessmentStore.getState().setError("err");
    useAssessmentStore.getState().setError(null);
    expect(useAssessmentStore.getState().error).toBeNull();
  });

  it("reset clears all state to defaults", () => {
    useAssessmentStore.getState().setSession("sess-x");
    useAssessmentStore.getState().setQuestion(sampleQuestion);
    useAssessmentStore.getState().setCompetencies(["a", "b"]);
    useAssessmentStore.getState().nextCompetency();
    useAssessmentStore.getState().incrementAnswered();
    useAssessmentStore.getState().setSubmitting(true);
    useAssessmentStore.getState().setError("boom");

    useAssessmentStore.getState().reset();

    const state = useAssessmentStore.getState();
    expect(state.sessionId).toBeNull();
    expect(state.currentQuestion).toBeNull();
    expect(state.selectedCompetencies).toEqual([]);
    expect(state.currentCompetencyIndex).toBe(0);
    expect(state.answeredCount).toBe(0);
    expect(state.isSubmitting).toBe(false);
    expect(state.error).toBeNull();
  });

  it("full assessment flow: set competencies → answer → next → answer → reset", () => {
    const store = useAssessmentStore;
    store.getState().setCompetencies(["comm", "lead"]);

    store.getState().setSession("sess-comm");
    store.getState().setQuestion(sampleQuestion);
    store.getState().incrementAnswered();
    store.getState().incrementAnswered();
    expect(store.getState().answeredCount).toBe(2);

    store.getState().nextCompetency();
    expect(store.getState().currentCompetencyIndex).toBe(1);
    expect(store.getState().answeredCount).toBe(0);
    expect(store.getState().sessionId).toBeNull();

    store.getState().setSession("sess-lead");
    store.getState().incrementAnswered();
    expect(store.getState().answeredCount).toBe(1);

    store.getState().reset();
    expect(store.getState().currentCompetencyIndex).toBe(0);
    expect(store.getState().sessionId).toBeNull();
  });
});
