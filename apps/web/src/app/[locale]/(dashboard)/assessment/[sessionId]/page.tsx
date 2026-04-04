"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { AnimatePresence } from "framer-motion";
import { useAssessmentStore } from "@/stores/assessment-store";
import type { Question, SessionState, AnswerFeedback } from "@/stores/assessment-store";
import { QuestionCard } from "@/components/assessment/question-card";
import { ProgressBar } from "@/components/assessment/progress-bar";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2, ChevronLeft } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { API_BASE } from "@/lib/api/client";
import { useTrackEvent } from "@/hooks/use-analytics";

type ScreenState = "question" | "transition" | "error";

const ESTIMATED_QUESTIONS = 8; // adaptive CAT — matches current pool size (8 MCQs per competency)
const DEFAULT_TIME_LIMIT_SECONDS = 120; // 2 minutes per question

export default function QuestionPage() {
  const { locale, sessionId } = useParams<{ locale: string; sessionId: string }>();
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);
  const questionStartTime = useRef<number>(Date.now()); // response time tracking for anti-gaming
  const currentLocale = i18n.language || locale;

  const {
    currentQuestion,
    selectedCompetencies,
    currentCompetencyIndex,
    answeredCount,
    isSubmitting,
    setQuestion,
    setSession,
    setSubmitting,
    incrementAnswered,
    nextCompetency,
    reset,
  } = useAssessmentStore();

  const track = useTrackEvent();

  const [answer, setAnswer] = useState("");
  const [screen, setScreen] = useState<ScreenState>("question");
  const [localError, setLocalError] = useState<string | null>(null);
  const [timingWarning, setTimingWarning] = useState<string | null>(null);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  const [isSlowFetch, setIsSlowFetch] = useState(false);
  // PROD-M01: Brief "Saved ✓" confirmation after successful answer submission
  const [answerSaved, setAnswerSaved] = useState(false);
  // Recovery state: shown when currentQuestion is null after 6s (e.g. refresh mid-session)
  const [isStuck, setIsStuck] = useState(false);

  // Show "Still working..." after 4s — LLM evaluation can take up to 8s
  useEffect(() => {
    if (!isSubmitting) {
      setIsSlowFetch(false);
      return;
    }
    const id = setTimeout(() => setIsSlowFetch(true), 4_000);
    return () => clearTimeout(id);
  }, [isSubmitting]);

  // Stuck-spinner detection: if currentQuestion is null for >6s on the question screen,
  // surface a recovery button instead of spinning forever (happens on refresh mid-session).
  useEffect(() => {
    if (currentQuestion || screen !== "question") {
      setIsStuck(false);
      return;
    }
    const id = setTimeout(() => {
      if (isMounted.current) setIsStuck(true);
    }, 6_000);
    return () => clearTimeout(id);
  }, [currentQuestion, screen]);

  const currentCompetency = selectedCompetencies[currentCompetencyIndex];
  const nextCompetencyName = selectedCompetencies[currentCompetencyIndex + 1];
  const isLastCompetency = currentCompetencyIndex >= selectedCompetencies.length - 1;

  // Guard: if store was cleared (direct URL access / page refresh), redirect to selection
  useEffect(() => {
    if (selectedCompetencies.length === 0) {
      router.replace(`/${currentLocale}/assessment`);
    }
  }, [selectedCompetencies.length, currentLocale, router]);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const getAuthHeader = useCallback(async () => {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      // Don't silently redirect — inform user their session expired
      if (isMounted.current) {
        setLocalError(t("assessment.sessionExpired", { defaultValue: "Your session has ended. Log in again to continue your progress." }));
      }
      setTimeout(() => router.push(`/${currentLocale}/login`), 3000);
      return null;
    }
    return `Bearer ${session.access_token}`;
  }, [router, currentLocale]);

  /**
   * Process the SessionState from an answer or start response.
   * Determines whether to show next question, transition, or complete.
   */
  const handleSessionUpdate = useCallback(
    (session: SessionState) => {
      if (!isMounted.current) return;

      if (session.is_complete || !session.next_question) {
        // This competency is done
        if (isLastCompetency) {
          router.push(`/${currentLocale}/assessment/${session.session_id}/complete`);
        } else {
          setScreen("transition");
        }
        return;
      }

      // Show next question — reset timer for response time tracking
      setQuestion(session.next_question);
      setAnswer("");
      setScreen("question");
      questionStartTime.current = Date.now();
    },
    [isLastCompetency, currentLocale, router, setQuestion]
  );

  /**
   * Submit the current answer via POST /assessment/answer.
   * The response includes the next question (or completion status).
   */
  const handleSubmit = useCallback(async () => {
    if (!currentQuestion || !answer.trim()) return;

    setSubmitting(true);
    setLocalError(null);
    setTimingWarning(null);

    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      const res = await fetch(
        `${API_BASE}/assessment/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: auth,
          },
          body: JSON.stringify({
            session_id: sessionId,
            question_id: currentQuestion.id,
            answer,
            response_time_ms: Date.now() - questionStartTime.current,
          }),
        }
      );

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const code = body?.detail?.code;
        if (code === "CONCURRENT_SUBMIT") {
          // Double-submit — ignore, question already moved forward
          return;
        }
        throw new Error("submit_failed");
      }

      const feedback = (await res.json()) as AnswerFeedback;

      if (!isMounted.current) return;

      // Show timing warning if backend flagged it
      if (feedback.timing_warning) {
        setTimingWarning(feedback.timing_warning);
      }

      // PROD-M01: Brief "Saved ✓" visual confirmation before next question renders
      setAnswerSaved(true);
      setTimeout(() => { if (isMounted.current) setAnswerSaved(false); }, 600);

      track("answer_submitted", {
        competency_slug: currentCompetency,
        question_id: currentQuestion.id,
        question_type: currentQuestion.question_type,
        answer_number: answeredCount + 1,
        response_time_ms: Date.now() - questionStartTime.current,
      }, sessionId);

      incrementAnswered();
      handleSessionUpdate(feedback.session);
    } catch {
      if (isMounted.current) {
        setLocalError(t("assessment.errorSubmitFailed"));
      }
    } finally {
      if (isMounted.current) {
        setSubmitting(false);
      }
    }
  }, [
    currentQuestion,
    answer,
    sessionId,
    getAuthHeader,
    setSubmitting,
    incrementAnswered,
    handleSessionUpdate,
    t,
  ]);

  /**
   * Skip the current question — submit empty-ish answer.
   */
  const handleSkip = useCallback(async () => {
    if (!currentQuestion) return;
    setLocalError(null);

    setSubmitting(true);
    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      const res = await fetch(
        `${API_BASE}/assessment/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: auth,
          },
          body: JSON.stringify({
            session_id: sessionId,
            question_id: currentQuestion.id,
            answer: "__SKIPPED__",
            response_time_ms: Date.now() - questionStartTime.current,
          }),
        }
      );

      if (res.ok) {
        const feedback = (await res.json()) as AnswerFeedback;
        if (isMounted.current) {
          incrementAnswered();
          handleSessionUpdate(feedback.session);
        }
      }
    } catch {
      // swallow — still usable
    } finally {
      if (isMounted.current) {
        setSubmitting(false);
      }
    }
  }, [currentQuestion, sessionId, getAuthHeader, setSubmitting, incrementAnswered, handleSessionUpdate]);

  /**
   * Start the next competency assessment (transition screen → next competency).
   */
  const handleNextCompetency = useCallback(async () => {
    setLocalError(null);
    setSubmitting(true);

    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      const res = await fetch(
        `${API_BASE}/assessment/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: auth,
          },
          body: JSON.stringify({ competency_slug: nextCompetencyName }),
        }
      );

      if (!res.ok) throw new Error("start_failed");

      const data = (await res.json()) as SessionState;
      // Advance competency index only after confirmed success — prevents stuck state on network error
      nextCompetency();
      setSession(data.session_id);

      if (data.next_question) {
        setQuestion(data.next_question);
        setAnswer("");
        setScreen("question");
        questionStartTime.current = Date.now();
      }

      router.replace(`/${currentLocale}/assessment/${data.session_id}`);
    } catch {
      setLocalError(t("assessment.errorStartFailed"));
    } finally {
      if (isMounted.current) setSubmitting(false);
    }
  }, [nextCompetency, nextCompetencyName, getAuthHeader, setSubmitting, setSession, setQuestion, router, currentLocale, t]);

  const handleLeave = () => {
    setShowLeaveConfirm(true);
  };

  const handleConfirmLeave = () => {
    setShowLeaveConfirm(false);
    reset();
    router.push(`/${currentLocale}/dashboard`);
  };

  // Get the display text for the current question based on locale
  const questionText = currentQuestion
    ? (currentLocale === "az" ? currentQuestion.question_az : currentQuestion.question_en)
    : "";

  // ── Render ──────────────────────────────────────────────────────────────

  if (screen === "transition") {
    const completedLabel = t("assessment.competencyComplete", {
      name: t(`competency.${currentCompetency}`, { defaultValue: currentCompetency }),
    });
    const continueLabel = t("assessment.continueToNext", {
      next: t(`competency.${nextCompetencyName}`, { defaultValue: nextCompetencyName }),
    });

    return (
      <div className="w-full mx-auto max-w-lg px-4 sm:px-6 py-8 space-y-4">
        {localError && (
          <Alert variant="destructive" role="alert">
            <AlertCircle className="size-4" aria-hidden="true" />
            <AlertDescription>{localError}</AlertDescription>
          </Alert>
        )}
        <div className="flex flex-col items-center text-center space-y-6 py-12">
          <div className="size-16 rounded-full bg-green-500/10 flex items-center justify-center">
            <svg className="size-8 text-green-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">{completedLabel}</h2>
            <p className="text-sm text-muted-foreground">{continueLabel}</p>
          </div>
          <Button onClick={handleNextCompetency} size="lg" className="w-full sm:w-auto min-h-[44px]" disabled={isSubmitting} aria-busy={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
                {t("common.loading")}
              </>
            ) : (
              t("assessment.continueButton", { defaultValue: "Continue" })
            )}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full mx-auto max-w-lg px-4 sm:px-6 py-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleLeave}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors min-h-[44px] min-w-[44px]"
          aria-label={t("common.back")}
        >
          <ChevronLeft className="size-4" aria-hidden="true" />
          {t("common.back")}
        </button>

        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {t(`competency.${currentCompetency}`, { defaultValue: currentCompetency })}
        </p>
      </div>

      {/* Progress */}
      <div className="space-y-1">
        <ProgressBar
          current={answeredCount}
          total={ESTIMATED_QUESTIONS}
          label={t("assessment.progress")}
        />
        <p className="text-xs text-muted-foreground" aria-live="polite">
          {t("assessment.questionProgress", {
            current: Math.min(answeredCount + 1, ESTIMATED_QUESTIONS),  // BATCH-O Q1: cap at total — prevents "9 of 8"
            total: ESTIMATED_QUESTIONS,
          })}
        </p>
      </div>

      {/* Timing warning from backend */}
      {timingWarning && (
        <Alert variant="destructive" role="alert">
          <AlertCircle className="size-4" aria-hidden="true" />
          <AlertDescription>{timingWarning}</AlertDescription>
        </Alert>
      )}

      {/* Error */}
      {localError && (
        <Alert variant="destructive" role="alert">
          <AlertCircle className="size-4" aria-hidden="true" />
          <AlertDescription>{localError}</AlertDescription>
        </Alert>
      )}

      {/* Main content */}
      <AnimatePresence mode="wait">
        {screen === "error" && (
          <div key="error" className="py-8 text-center space-y-4">
            <p className="text-sm text-muted-foreground">{localError}</p>
            <Button onClick={() => setScreen("question")} variant="outline">
              {t("common.tryAgain")}
            </Button>
          </div>
        )}

        {screen === "question" && currentQuestion && (
          <QuestionCard
            key={currentQuestion.id}
            question={currentQuestion}
            questionText={questionText}
            questionIndex={answeredCount}
            answer={answer}
            onAnswerChange={setAnswer}
            disabled={isSubmitting}
          />
        )}

        {screen === "question" && !currentQuestion && (
          <div key="loading" className="flex flex-col items-center justify-center gap-4 py-12 text-center">
            {isStuck ? (
              <>
                <p className="text-sm text-muted-foreground">
                  {t("assessment.refreshedMidSession", {
                    defaultValue: "It looks like you refreshed mid-assessment. Your progress is saved.",
                  })}
                </p>
                <Button
                  variant="outline"
                  onClick={() => router.replace(`/${currentLocale}/assessment`)}
                >
                  {t("assessment.returnToSelection", { defaultValue: "Return to competency selection" })}
                </Button>
              </>
            ) : (
              <Loader2 className="size-8 animate-spin text-primary" aria-label={t("common.loading")} />
            )}
          </div>
        )}
      </AnimatePresence>

      {/* Actions */}
      {screen === "question" && currentQuestion && (
        <div className="flex flex-col gap-2 pt-2">
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !answer.trim()}
            size="lg"
            className="w-full"
            aria-busy={isSubmitting}
          >
            {answerSaved ? (
              <span className="flex items-center gap-1.5">
                <svg className="size-4 text-green-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                {t("assessment.answerSaved", { defaultValue: "Saved" })}
              </span>
            ) : isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
                {isSlowFetch ? t("assessment.stillWorking") : t("common.loading")}
              </>
            ) : (
              t("assessment.submit")
            )}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground min-h-[44px]"
            onClick={handleSkip}
            disabled={isSubmitting}
          >
            {t("assessment.skipQuestion")}
          </Button>
        </div>
      )}

      {/* Leave confirmation modal — replaces window.confirm (ADHD-first, accessible) */}
      {showLeaveConfirm && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="leave-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
        >
          <div className="w-full max-w-sm rounded-2xl bg-surface-container-low p-6 shadow-xl space-y-4">
            <h2 id="leave-dialog-title" className="text-base font-bold text-on-surface">
              {t("assessment.leaveTitle")}
            </h2>
            <p className="text-sm text-on-surface-variant">
              {t("assessment.leaveWarning")}
            </p>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button
                variant="outline"
                size="sm"
                className="w-full sm:w-auto min-h-[44px]"
                onClick={() => setShowLeaveConfirm(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="w-full sm:w-auto min-h-[44px]"
                onClick={handleConfirmLeave}
              >
                {t("assessment.leaveConfirm")}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
