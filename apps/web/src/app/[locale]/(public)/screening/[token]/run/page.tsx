"use client";

/**
 * Campaign-scoped anonymous assessment runner.
 *
 * Usage: /{locale}/screening/{token}/run
 *
 * Brings apps/v2's anonymous candidate runner into the real app. The flow:
 *   consent → (anon session is already provisioned by the landing) → join
 *   (idempotent) → start each competency WITH its assigned session_id → answer
 *   loop → integrity snapshot → complete → next competency → done, with
 *   SESSION_IN_PROGRESS / SESSION_NOT_ACTIVATABLE resume.
 *
 * Why a dedicated route (not the /(dashboard)/assessment self-serve picker):
 * the campaign join pre-creates `assigned` sessions per competency. They must
 * be ACTIVATED by /assessment/start WITH session_id (backend assessment.py:290),
 * otherwise a fresh off-campaign session is created that never appears in the
 * org's candidate report (counted by campaign_id). See V2 ANON SPEC.
 *
 * Auth: apiFetch auto-injects the (anonymous) Supabase JWT via getFreshAccessToken.
 * No org/admin surface is reachable — backend scopes every query to the caller's
 * own UUID; an anon user owns no org and has no profile row.
 *
 * Foundation Laws: no red (#D4B4FF for errors), one primary CTA per phase,
 * i18n inline t(key,{defaultValue}), no spinner (Skeleton placeholders),
 * Full/Mid/Low energy modes, prefers-reduced-motion respected via static markup.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, ApiError } from "@/lib/api/client";
import { createClient } from "@/lib/supabase/client";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { IntegrityWatcher } from "@/lib/assessment/integrity";
import type { JoinedSession, CampaignJoinResult } from "@/hooks/queries/use-campaigns";

interface QuestionOut {
  id: string;
  question_type: string;
  question_en: string;
  question_az: string;
  question_ru?: string | null;
  options: { key: string; text_en?: string; text_az?: string; text_ru?: string }[] | null;
}
interface SessionOut {
  session_id: string;
  competency_slug: string;
  questions_answered: number;
  is_complete: boolean;
  next_question: QuestionOut | null;
}
interface AnswerFeedback {
  session_id: string;
  timing_warning: string | null;
  session: SessionOut;
}

type Phase = "consent" | "preparing" | "question" | "switching" | "done" | "error";

const CAMERA_START_TIMEOUT_MS = 6000;

/** sessionStorage key carrying the joined sessions from the landing → runner hop. */
function planKey(token: string) {
  return `volaura-screening-plan:${token}`;
}

export default function ScreeningRunnerPage() {
  const { locale, token } = useParams<{ locale: string; token: string }>();
  const router = useRouter();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { energy, setEnergy } = useEnergyMode();
  const isLow = energy === "low";

  const [phase, setPhase] = useState<Phase>("consent");
  const [errorMsg, setErrorMsg] = useState("");
  const [plan, setPlan] = useState<JoinedSession[]>([]);
  const [planIndex, setPlanIndex] = useState(0);
  const [session, setSession] = useState<SessionOut | null>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [camDenied, setCamDenied] = useState(false);

  const watcher = useRef<IntegrityWatcher | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const questionShownAt = useRef(0);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      watcher.current?.stop();
    };
  }, []);

  const fail = useCallback((e: unknown) => {
    if (!isMounted.current) return;
    const msg =
      e instanceof ApiError
        ? e.detail
        : e instanceof Error
          ? e.message
          : String(e);
    setErrorMsg(msg);
    setPhase("error");
  }, []);

  const questionText = useCallback(
    (q: QuestionOut) =>
      lang === "az" && q.question_az
        ? q.question_az
        : lang === "ru" && q.question_ru
          ? q.question_ru
          : q.question_en,
    [lang],
  );

  // Activate (or resume) the competency at `index`. Mirrors apps/v2 run/page.tsx.
  const startCompetency = useCallback(
    async (sessions: JoinedSession[], index: number) => {
      const target = sessions[index];
      const slugs = sessions.map((s) => s.competency_slug);
      try {
        const out = await apiFetch<SessionOut>("/assessment/start", {
          method: "POST",
          body: JSON.stringify({
            competency_slug: target.competency_slug,
            session_id: target.session_id,
            automated_decision_consent: true,
            assessment_plan_competencies: slugs,
            assessment_plan_current_index: index,
            energy_level: energy,
            language: lang,
          }),
        });
        if (!isMounted.current) return;
        setSession(out);
        questionShownAt.current = Date.now();
        setPhase("question");
      } catch (e) {
        const err = e as ApiError;
        if (err.code === "SESSION_IN_PROGRESS" || err.code === "SESSION_NOT_ACTIVATABLE") {
          // already active or completed — resume the open question, or skip forward
          const resumed = await apiFetch<SessionOut & { status: string }>(
            `/assessment/session/${target.session_id}`,
          );
          if (resumed.next_question) {
            if (!isMounted.current) return;
            setSession({ ...resumed, is_complete: false });
            questionShownAt.current = Date.now();
            setPhase("question");
            return;
          }
          if (index + 1 < sessions.length) {
            setPlanIndex(index + 1);
            await startCompetency(sessions, index + 1);
            return;
          }
          if (isMounted.current) setPhase("done");
          return;
        }
        fail(e);
      }
    },
    [energy, lang, fail],
  );

  const begin = useCallback(async () => {
    setPhase("preparing");
    try {
      // Ensure an (anonymous) session exists — the landing normally provisions it,
      // but a direct deep-link / reload to /run must self-provision too.
      const supabase = createClient();
      const { data: sess } = await supabase.auth.getSession();
      if (!sess.session) {
        const { error } = await supabase.auth.signInAnonymously();
        if (error) {
          fail(new Error(error.message));
          return;
        }
      }

      // Camera must never block the assessment. Race getUserMedia against a short
      // timeout so /join and /assessment/start always fire.
      watcher.current = new IntegrityWatcher();
      if (videoRef.current) {
        const started = watcher.current.start(videoRef.current);
        const outcome = await Promise.race([
          started.catch(() => false as const),
          new Promise<"timeout">((resolve) => setTimeout(() => resolve("timeout"), CAMERA_START_TIMEOUT_MS)),
        ]);
        if (outcome !== true && isMounted.current) setCamDenied(true);
      }

      // Reuse the joined sessions handed over by the landing if present; otherwise
      // join here (idempotent server-side — one session per competency per campaign).
      let pending: JoinedSession[] = [];
      try {
        const raw = sessionStorage.getItem(planKey(token));
        if (raw) pending = JSON.parse(raw) as JoinedSession[];
      } catch {
        pending = [];
      }
      if (pending.length === 0) {
        const joined = await apiFetch<CampaignJoinResult>(
          `/campaigns/public/${encodeURIComponent(token)}/join`,
          { method: "POST" },
        );
        pending = joined.sessions;
      }

      if (pending.length === 0) {
        if (isMounted.current) setPhase("done");
        return;
      }
      setPlan(pending);
      setPlanIndex(0);
      await startCompetency(pending, 0);
    } catch (e) {
      fail(e);
    }
  }, [token, startCompetency, fail]);

  const finishSession = useCallback(
    async (sessionId: string) => {
      setPhase("switching");
      try {
        const flags = watcher.current?.snapshot();
        if (flags) {
          await apiFetch(`/assessment/${sessionId}/integrity`, {
            method: "POST",
            body: JSON.stringify(flags),
          }).catch(() => undefined);
        }
        await apiFetch(`/assessment/complete/${sessionId}`, { method: "POST" });
        const next = planIndex + 1;
        if (next < plan.length) {
          setPlanIndex(next);
          await startCompetency(plan, next);
        } else {
          watcher.current?.stop();
          // Clear the handover so a later visit re-joins fresh state.
          try {
            sessionStorage.removeItem(planKey(token));
          } catch {
            /* ignore */
          }
          if (isMounted.current) setPhase("done");
        }
      } catch (e) {
        fail(e);
      }
    },
    [plan, planIndex, startCompetency, token, fail],
  );

  const submit = useCallback(async () => {
    if (!session?.next_question || !answer.trim() || submitting) return;
    setSubmitting(true);
    const elapsed = Math.min(Math.max(Date.now() - questionShownAt.current, 0), 600000);
    try {
      const fb = await apiFetch<AnswerFeedback>("/assessment/answer", {
        method: "POST",
        body: JSON.stringify({
          session_id: session.session_id,
          question_id: session.next_question.id,
          answer: answer.trim(),
          response_time_ms: elapsed,
        }),
      });
      if (!isMounted.current) return;
      setAnswer("");
      if (fb.session.is_complete || !fb.session.next_question) {
        await finishSession(session.session_id);
      } else {
        setSession(fb.session);
        questionShownAt.current = Date.now();
      }
    } catch (e) {
      fail(e);
    } finally {
      if (isMounted.current) setSubmitting(false);
    }
  }, [session, answer, submitting, finishSession, fail]);

  const q = session?.next_question ?? null;
  const isMcq = Boolean(q?.options?.length);
  const total = plan.length;
  const progressLabel =
    total > 0 && phase !== "done"
      ? t("screening.runProgress", {
          defaultValue: "Competency {{current}} of {{total}}",
          current: planIndex + 1,
          total,
        })
      : null;

  // ── Header: energy modes + progress ────────────────────────────────────────
  const header = (
    <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-2xl flex-wrap items-center justify-between gap-3 px-6 py-3">
        <span className="text-base font-black tracking-tight text-foreground">VOLAURA</span>
        <div className="flex items-center gap-2 text-xs font-medium">
          {progressLabel && (
            <span className="hidden text-muted-foreground sm:inline" aria-live="polite">
              {progressLabel}
            </span>
          )}
          <div
            className="flex rounded-full border border-border bg-muted/40 p-1"
            role="group"
            aria-label={t("assessment.energyLabel", { defaultValue: "Energy level" })}
          >
            {(["full", "mid", "low"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                aria-pressed={energy === mode}
                onClick={() => setEnergy(mode)}
                className={`rounded-full px-3 py-1 transition-colors ${
                  energy === mode
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {t(`assessment.energy.${mode}`, {
                  defaultValue: mode === "full" ? "Full" : mode === "mid" ? "Mid" : "Low",
                })}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );

  return (
    <div className="min-h-screen bg-background text-foreground" data-energy={energy}>
      {header}

      <main className={`mx-auto max-w-2xl px-6 pb-20 ${isLow ? "pt-8" : "pt-12"}`}>
        {/* Camera strip — small, honest, never blocks. Hidden on consent/done. */}
        <div
          className={
            phase === "consent" || phase === "done"
              ? "hidden"
              : "mb-6 flex items-center gap-3 rounded-2xl border border-border bg-card p-3"
          }
        >
          <video
            ref={videoRef}
            muted
            playsInline
            className="h-16 w-20 rounded-xl border border-border object-cover"
          />
          <p className="text-xs leading-snug text-muted-foreground">
            {camDenied
              ? t("screening.camDenied", {
                  defaultValue: "Continuing without camera — this will be noted in the report.",
                })
              : t("screening.camNote", { defaultValue: "Video stays in your browser. Nothing is uploaded." })}
          </p>
        </div>

        {/* ── Consent ── */}
        {phase === "consent" && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="rounded-3xl border border-border bg-card p-6"
          >
            <div className="mb-5 inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              {t("screening.tierLabel", { defaultValue: "Assessment Completed" })}
            </div>
            <h1 className="text-2xl font-bold font-headline tracking-tight text-foreground">
              {t("screening.consentTitle", { defaultValue: "Before you start" })}
            </h1>

            <div className="mt-5 space-y-3">
              <details
                open
                className="rounded-2xl border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground"
              >
                <summary className="cursor-pointer list-none font-semibold text-foreground">
                  {t("screening.consentScoreTitle", { defaultValue: "AI score and human decision" })}
                </summary>
                <p className="mt-2 text-[13px] leading-relaxed">
                  {t("screening.consentBody", {
                    defaultValue:
                      "This assessment produces an automated score (your AURA score). The result only SUPPORTS an organization's decision — it does not make it. A human makes the final decision.",
                  })}
                </p>
              </details>
              <details className="rounded-2xl border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
                <summary className="cursor-pointer list-none font-semibold text-foreground">
                  {t("screening.cameraTitle", { defaultValue: "Camera integrity signal" })}
                </summary>
                <p className="mt-2 text-[13px] leading-relaxed">
                  {t("screening.cameraBody", {
                    defaultValue:
                      "Your camera will be on for integrity. Video is never uploaded or stored — it is processed only in your browser.",
                  })}
                </p>
              </details>
              <details className="rounded-2xl border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
                <summary className="cursor-pointer list-none font-semibold text-foreground">
                  {t("screening.rightsTitle", { defaultValue: "Your rights" })}
                </summary>
                <p className="mt-2 text-[13px] leading-relaxed">
                  {t("screening.rightsBody", {
                    defaultValue:
                      "You may contest the automated scoring and request review by a human. This is not a hiring decision and not a substitute for professional certification. Participation is voluntary.",
                  })}
                </p>
              </details>
            </div>

            <button
              onClick={begin}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-8 py-4 text-base font-semibold text-primary-foreground shadow-md transition-all hover:bg-primary/90"
            >
              {t("screening.agreeStart", { defaultValue: "I agree — start" })}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </motion.div>
        )}

        {/* ── Preparing / switching (Skeleton, no spinner) ── */}
        {(phase === "preparing" || phase === "switching") && (
          <div className="mt-6 space-y-3" role="status" aria-live="polite">
            <Skeleton className="h-6 w-2/5 rounded-md" />
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
            <p className="text-xs text-muted-foreground">
              {phase === "preparing"
                ? t("screening.preparing", { defaultValue: "Preparing…" })
                : t("screening.switching", { defaultValue: "Next competency…" })}
            </p>
          </div>
        )}

        {/* ── Question ── */}
        {phase === "question" && q && (
          <div className="mt-6">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              {t(`competency.${session?.competency_slug}`, {
                defaultValue: (session?.competency_slug ?? "").replace(/_/g, " "),
              })}{" "}
              · #{(session?.questions_answered ?? 0) + 1}
            </p>
            <h2 className="mt-3 text-xl font-semibold font-headline leading-snug text-foreground">
              {questionText(q)}
            </h2>

            {isMcq ? (
              <div className="mt-6 space-y-2">
                {q.options!.map((opt) => {
                  const text =
                    lang === "az" && opt.text_az
                      ? opt.text_az
                      : lang === "ru" && opt.text_ru
                        ? opt.text_ru
                        : opt.text_en || opt.key;
                  const selected = answer === opt.key;
                  return (
                    <button
                      key={opt.key}
                      onClick={() => setAnswer(opt.key)}
                      className={`block w-full rounded-xl border px-4 py-3 text-left text-sm transition-colors ${
                        selected
                          ? "border-primary bg-primary/10 text-foreground"
                          : "border-border bg-card text-muted-foreground hover:border-primary/50"
                      }`}
                    >
                      {text}
                    </button>
                  );
                })}
              </div>
            ) : (
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={t("screening.answerPlaceholder", { defaultValue: "Type your answer…" })}
                rows={6}
                maxLength={5000}
                className="mt-6 w-full rounded-xl border border-border bg-card p-4 text-sm leading-relaxed text-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary"
              />
            )}

            <button
              onClick={submit}
              disabled={!answer.trim() || submitting}
              className="mt-6 flex w-full items-center justify-center rounded-xl bg-primary px-6 py-3.5 text-center text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting
                ? t("common.loading", { defaultValue: "Loading…" })
                : t("screening.submit", { defaultValue: "Submit answer" })}
            </button>
          </div>
        )}

        {/* ── Done ── */}
        {phase === "done" && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 rounded-3xl border border-border bg-card p-7"
          >
            <div className="mb-5 inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              {t("screening.tierLabel", { defaultValue: "Assessment Completed" })}
            </div>
            <h1 className="text-2xl font-bold font-headline tracking-tight text-foreground">
              {t("screening.doneTitle", { defaultValue: "All done!" })}
            </h1>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              {t("screening.doneBody", {
                defaultValue:
                  "Your answers are being scored. The organization will see your results in their report. Keep this link.",
              })}
            </p>
            <button
              onClick={() => router.push(`/${locale}`)}
              className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-background px-6 py-3 text-sm font-medium text-muted-foreground transition-all hover:bg-accent"
            >
              {t("screening.goHome", { defaultValue: "Go to VOLAURA home" })}
            </button>
          </motion.div>
        )}

        {/* ── Error (no red — purple per Foundation Law 1) ── */}
        {phase === "error" && (
          <div className="mt-6 rounded-3xl border border-border bg-card p-7">
            <div className="mb-4 inline-flex items-center gap-2 text-[#D4B4FF]">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
              <h1 className="text-lg font-bold">
                {t("screening.errorTitle", { defaultValue: "Something went wrong" })}
              </h1>
            </div>
            <p className="break-words text-sm text-muted-foreground">{errorMsg}</p>
            <button
              onClick={() => {
                setErrorMsg("");
                setPhase("consent");
              }}
              className="mt-6 inline-flex items-center justify-center rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
            >
              {t("common.tryAgain", { defaultValue: "Try again" })}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
