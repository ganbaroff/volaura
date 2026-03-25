"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { AnimatePresence } from "framer-motion";
import { useAssessmentStore } from "@/stores/assessment-store";
import { QuestionCard } from "@/components/assessment/question-card";
import { ProgressBar } from "@/components/assessment/progress-bar";
import { Timer } from "@/components/assessment/timer";
import { TransitionScreen } from "@/components/assessment/transition-screen";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2, ChevronLeft } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import type { Question } from "@/stores/assessment-store";

type ScreenState = "question" | "evaluating" | "transition" | "error";

const ESTIMATED_QUESTIONS = 10; // adaptive CAT — shown as progress estimate

export default function QuestionPage() {
  const { locale, sessionId } = useParams<{ locale: string; sessionId: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);

  const {
    currentQuestion,
    selectedCompetencies,
    currentCompetencyIndex,
    answeredCount,
    isSubmitting,
    setQuestion,
    setSession,
    setSubmitting,
    setEvaluating,
    incrementAnswered,
    nextCompetency,
    reset,
  } = useAssessmentStore();

  const [answer, setAnswer] = useState("");
  const [screen, setScreen] = useState<ScreenState>("question");
  const [localError, setLocalError] = useState<string | null>(null);
  const [timerKey, setTimerKey] = useState(0); // reset timer when question changes

  const currentCompetency = selectedCompetencies[currentCompetencyIndex];
  const nextCompetencyName = selectedCompetencies[currentCompetencyIndex + 1];
  const isLastCompetency = currentCompetencyIndex >= selectedCompetencies.length - 1;

  // Guard: if store was cleared (direct URL access / page refresh), redirect to selection
  useEffect(() => {
    if (selectedCompetencies.length === 0) {
      router.replace(`/${locale}/assessment`);
    }
  }, [selectedCompetencies.length, locale, router]);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Fetch first question on mount if not already loaded
  useEffect(() => {
    if (!currentQuestion) {
      fetchNextQuestion();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getAuthHeader = useCallback(async () => {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      router.push(`/${locale}/login`);
      return null;
    }
    return `Bearer ${session.access_token}`;
  }, [router, locale]);

  const fetchNextQuestion = useCallback(async () => {
    setLocalError(null);
    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/assessments/${sessionId}/next-question`,
        { headers: { Authorization: auth } }
      );

      if (res.status === 404) {
        // No more questions — competency complete
        if (isLastCompetency) {
          router.push(`/${locale}/assessment/${sessionId}/complete`);
        } else {
          setScreen("transition");
        }
        return;
      }

      if (!res.ok) {
        throw new Error("load_failed");
      }

      const q = (await res.json()) as Question;
      setQuestion(q);
      setAnswer("");
      setTimerKey((k) => k + 1);
      setScreen("question");
    } catch {
      setLocalError(t("assessment.errorLoadingQuestion"));
      setScreen("error");
    }
  }, [sessionId, isLastCompetency, getAuthHeader, setQuestion, t, router]);

  const handleSubmit = useCallback(async () => {
    if (!currentQuestion || !answer.trim()) return;

    setSubmitting(true);
    setLocalError(null);

    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/assessments/${sessionId}/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: auth,
          },
          body: JSON.stringify({
            question_id: currentQuestion.id,
            answer,
          }),
        }
      );

      if (!res.ok) {
        throw new Error("submit_failed");
      }

      // 202 Accepted — LLM evaluating asynchronously
      if (res.status === 202) {
        setEvaluating(true);
        setScreen("evaluating");
        // Poll for result
        await pollForResult(auth);
        return;
      }

      incrementAnswered();
      await fetchNextQuestion();
    } catch {
      setLocalError(t("assessment.errorSubmitFailed"));
    } finally {
      setSubmitting(false);
    }
  }, [
    currentQuestion,
    answer,
    sessionId,
    getAuthHeader,
    setSubmitting,
    setEvaluating,
    incrementAnswered,
    fetchNextQuestion,
    t,
  ]);

  const pollForResult = useCallback(
    async (auth: string) => {
      const maxAttempts = 15;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        if (!isMounted.current) return; // component unmounted — stop polling

        try {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/assessments/${sessionId}/status`,
            { headers: { Authorization: auth } }
          );

          if (res.ok) {
            const data = (await res.json()) as { status: string };
            if (data.status === "ready") {
              if (!isMounted.current) return;
              setEvaluating(false);
              incrementAnswered();
              await fetchNextQuestion();
              return;
            }
          }
        } catch {
          // network hiccup — keep retrying
        }

        await new Promise((r) => setTimeout(r, 2000));
      }

      // Exhausted retries
      if (isMounted.current) {
        setEvaluating(false);
        setLocalError(t("assessment.errorSubmitFailed"));
        setScreen("error");
      }
    },
    [sessionId, setEvaluating, incrementAnswered, fetchNextQuestion, t]
  );

  const handleTimerExpire = useCallback(async () => {
    // Auto-submit blank on timer expiry
    if (!currentQuestion) return;
    setLocalError(null);

    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/assessments/${sessionId}/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: auth,
          },
          body: JSON.stringify({
            question_id: currentQuestion.id,
            answer: answer || "__TIMEOUT__",
          }),
        }
      );
    } catch {
      // swallow — still move forward
    }

    incrementAnswered();
    await fetchNextQuestion();
  }, [currentQuestion, sessionId, answer, getAuthHeader, incrementAnswered, fetchNextQuestion]);

  const handleNextCompetency = useCallback(async () => {
    nextCompetency();
    setLocalError(null);

    try {
      const auth = await getAuthHeader();
      if (!auth) return;

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/assessments/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: auth,
          },
          body: JSON.stringify({ competency: nextCompetencyName }),
        }
      );

      if (!res.ok) throw new Error("start_failed");

      const data = (await res.json()) as { session_id: string };
      setSession(data.session_id);
      router.replace(`/${locale}/assessment/${data.session_id}`);
    } catch {
      setLocalError(t("assessment.errorStartFailed"));
    }
  }, [nextCompetency, nextCompetencyName, getAuthHeader, setSession, router, t]);

  const handleLeave = () => {
    if (window.confirm(t("assessment.leaveWarning"))) {
      reset();
      router.push(`/${locale}/dashboard`);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────

  if (screen === "transition") {
    const completedLabel = t("assessment.competencyComplete", {
      name: t(`competency.${currentCompetency}`, { defaultValue: currentCompetency }),
    });
    const continueLabel = t("assessment.continueToNext", {
      next: t(`competency.${nextCompetencyName}`, { defaultValue: nextCompetencyName }),
    });

    return (
      <div className="mx-auto max-w-lg px-4 py-8">
        <TransitionScreen
          completedLabel={completedLabel}
          continueLabel={continueLabel}
          onContinue={handleNextCompetency}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleLeave}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          aria-label={t("common.back")}
        >
          <ChevronLeft className="size-4" aria-hidden="true" />
          {t("common.back")}
        </button>

        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {t(`competency.${currentCompetency}`, { defaultValue: currentCompetency })}
        </p>

        {currentQuestion && (
          <Timer
            key={timerKey}
            totalSeconds={currentQuestion.time_limit_seconds}
            onExpire={handleTimerExpire}
            label={t("assessment.timeRemaining")}
          />
        )}
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
            current: answeredCount + 1,
            total: ESTIMATED_QUESTIONS,
          })}
        </p>
      </div>

      {/* Error */}
      {localError && (
        <Alert variant="destructive" role="alert">
          <AlertCircle className="size-4" aria-hidden="true" />
          <AlertDescription>{localError}</AlertDescription>
        </Alert>
      )}

      {/* Main content */}
      <AnimatePresence mode="wait">
        {screen === "evaluating" && (
          <div
            key="evaluating"
            className="flex flex-col items-center gap-3 py-12 text-center"
            role="status"
            aria-live="polite"
          >
            <Loader2 className="size-8 animate-spin text-primary" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">{t("assessment.evaluating")}</p>
          </div>
        )}

        {screen === "error" && (
          <div key="error" className="py-8 text-center space-y-4">
            <p className="text-sm text-muted-foreground">{localError}</p>
            <Button onClick={fetchNextQuestion} variant="outline">
              {t("common.tryAgain")}
            </Button>
          </div>
        )}

        {screen === "question" && currentQuestion && (
          <QuestionCard
            key={currentQuestion.id}
            question={currentQuestion}
            questionIndex={answeredCount}
            answer={answer}
            onAnswerChange={setAnswer}
            disabled={isSubmitting}
          />
        )}

        {screen === "question" && !currentQuestion && (
          <div key="loading" className="flex justify-center py-12">
            <Loader2 className="size-8 animate-spin text-primary" aria-label={t("common.loading")} />
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
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
                {t("common.loading")}
              </>
            ) : (
              t("assessment.submit")
            )}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            onClick={handleTimerExpire}
            disabled={isSubmitting}
          >
            {t("assessment.skipQuestion")}
          </Button>
        </div>
      )}
    </div>
  );
}
