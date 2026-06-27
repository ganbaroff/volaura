"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, track } from "@/lib/client";
import { IntegrityWatcher } from "@/lib/integrity";

/*
  Candidate assessment runner — the whole journey stays on this host.
  Pilot session = anonymous Supabase auth bound to the invite token (NOT the
  identity layer; SİMA identity verification is a future layer and we never
  claim "identity verified" until it ships). Camera anti-cheat per Gap 9:
  client-side only, soft flags, zero video upload.
*/

interface JoinedSession {
  session_id: string;
  competency_slug: string;
  status: string;
}
interface QuestionOut {
  id: string;
  question_type: string;
  question_en: string;
  question_az: string;
  options: { key: string; text_en?: string; text_az?: string }[] | null;
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

type Lang = "az" | "en";
type EnergyMode = "full" | "mid" | "low";
type Phase = "consent" | "preparing" | "question" | "switching" | "done" | "error";

const ENERGY_LABELS: Record<EnergyMode, { az: string; en: string }> = {
  full: { az: "Tam", en: "Full" },
  mid: { az: "Orta", en: "Mid" },
  low: { az: "Sakit", en: "Low" },
};

const STRINGS = {
  az: {
    title: "Qiymətləndirmə",
    consentTitle: "Başlamazdan əvvəl",
    consentBody:
      "Bu qiymətləndirmə avtomatik bal (AURA) çıxarır. Nəticə təşkilatın qərarına yalnız KÖMƏK edir — onu əvəz etmir. Yekun qərarı insan verir.",
    cameraBody:
      "Dürüstlük üçün kamera aktiv olacaq. Video heç yerə göndərilmir və saxlanılmır — yalnız brauzerinizdə işlənir.",
    rightsBody:
      "Hüquqlarınız: avtomatik qiymətləndirməyə etiraz edə və insan tərəfindən yenidən baxılmasını tələb edə bilərsiniz. Bu işə qəbul qərarı deyil və peşəkar sertifikatı əvəz etmir. İştirak könüllüdür.",
    agree: "Qəbul edirəm — başla",
    preparing: "Hazırlanır…",
    submit: "Cavabı göndər",
    open_placeholder: "Cavabınızı yazın…",
    switching: "Növbəti bacarıq…",
    doneTitle: "Hazırdır!",
    doneBody: "Cavablarınız qiymətləndirilir. Təşkilat nəticələri hesabatda görəcək. Bu linki saxlayın.",
    error: "Xəta baş verdi",
    retry: "Yenidən cəhd et",
    camDenied: "Kamera olmadan davam edirsiniz — bu, hesabatda qeyd olunacaq.",
    tierLabel: "Assessment Completed",
    tierBody:
      "Şəxsiyyət təsdiqi hələ qoşulmadığı üçün bu sessiya “Verified Skills” kimi göstərilməyəcək.",
    atlasHint: "Atlas yalnız lazım olanı göstərir. Aşağı enerji rejimində ekran daha sakit olur.",
    progress: (a: number, t: number) => `Bacarıq ${a} / ${t}`,
  },
  en: {
    title: "Assessment",
    consentTitle: "Before you start",
    consentBody:
      "This assessment produces an automated score (your AURA score). The result only SUPPORTS an organization's decision — it does not make it. A human makes the final decision.",
    cameraBody:
      "Your camera will be on for integrity. Video is never uploaded or stored — it is processed only in your browser.",
    rightsBody:
      "Your rights: you may contest the automated scoring and request review by a human. This is not a hiring decision and not a substitute for professional certification. Participation is voluntary.",
    agree: "I agree — start",
    preparing: "Preparing…",
    submit: "Submit answer",
    open_placeholder: "Type your answer…",
    switching: "Next competency…",
    doneTitle: "All done!",
    doneBody: "Your answers are being scored. The organization will see your results in their report. Keep this link.",
    error: "Something went wrong",
    retry: "Try again",
    camDenied: "Continuing without camera — this will be noted in the report.",
    tierLabel: "Assessment Completed",
    tierBody:
      "Because identity assurance is not connected yet, this session will not be shown as “Verified Skills”.",
    atlasHint: "Atlas keeps the screen focused. Low energy mode makes the page quieter.",
    progress: (a: number, t: number) => `Competency ${a} of ${t}`,
  },
} as const;

function ScreeningHeader({
  lang,
  setLang,
  energy,
  setEnergy,
  progress,
}: {
  lang: Lang;
  setLang: (lang: Lang) => void;
  energy: EnergyMode;
  setEnergy: (energy: EnergyMode) => void;
  progress?: string;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-rule/50 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-[680px] flex-wrap items-center justify-between gap-3 px-6 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-gradient-to-br from-seal to-[#a78bfa] text-sm font-bold text-white">
            V
          </span>
          <span className="font-display text-base font-bold tracking-tight">VOLAURA</span>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium">
          {progress && <span className="hidden text-ink-faint sm:inline">{progress}</span>}
          <div className="flex rounded-full border border-rule bg-paper-sunken p-1">
            {(Object.keys(ENERGY_LABELS) as EnergyMode[]).map((mode) => (
              <button
                key={mode}
                type="button"
                aria-pressed={energy === mode}
                onClick={() => setEnergy(mode)}
                className={`rounded-full px-3 py-1 transition-colors ${
                  energy === mode ? "bg-seal text-white" : "text-ink-faint hover:text-ink"
                }`}
              >
                {ENERGY_LABELS[mode][lang]}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setLang(lang === "az" ? "en" : "az")}
            className="rounded-full border border-rule bg-paper-sunken px-3 py-2 text-ink-soft transition-colors hover:border-seal hover:text-ink"
          >
            {lang === "az" ? "EN" : "AZ"}
          </button>
        </div>
      </div>
    </header>
  );
}

function ConsentDisclosure({
  title,
  body,
  defaultOpen = false,
}: {
  title: string;
  body: string;
  defaultOpen?: boolean;
}) {
  return (
    <details
      open={defaultOpen}
      className="rounded-[14px] border border-rule bg-paper-sunken px-4 py-3 text-sm text-ink-soft"
    >
      <summary className="cursor-pointer list-none font-semibold text-ink">
        {title}
      </summary>
      <p className="mt-2 text-[13px] leading-relaxed">{body}</p>
    </details>
  );
}

export default function RunnerPage({ params }: { params: { token: string } }) {
  const { token } = params;
  const [lang, setLang] = useState<Lang>("az");
  const [energy, setEnergy] = useState<EnergyMode>("full");
  const [phase, setPhase] = useState<Phase>("consent");
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<JoinedSession[]>([]);
  const [planIndex, setPlanIndex] = useState(0);
  const [session, setSession] = useState<SessionOut | null>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [camDenied, setCamDenied] = useState(false);
  const watcher = useRef<IntegrityWatcher | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const questionShownAt = useRef(0);
  const t = STRINGS[lang];

  const fail = (e: unknown) => {
    setError(e instanceof Error ? e.message : String(e));
    setPhase("error");
  };

  const startCompetency = useCallback(
    async (sessions: JoinedSession[], index: number) => {
      const target = sessions[index];
      const slugs = sessions.map((s) => s.competency_slug);
      try {
        const out = await api<SessionOut>("/assessment/start", {
          json: {
            competency_slug: target.competency_slug,
            session_id: target.session_id,
            automated_decision_consent: true,
            assessment_plan_competencies: slugs,
            assessment_plan_current_index: index,
            energy_level: energy,
            language: lang,
          },
        });
        setSession(out);
        questionShownAt.current = Date.now();
        setPhase("question");
      } catch (e) {
        const err = e as Error & { code?: string };
        if (err.code === "SESSION_IN_PROGRESS" || err.code === "SESSION_NOT_ACTIVATABLE") {
          // already active or completed — resume or skip forward
          const resumed = await api<SessionOut & { status: string }>(`/assessment/session/${target.session_id}`);
          if (resumed.next_question) {
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
          setPhase("done");
          return;
        }
        fail(e);
      }
    },
    [energy, lang],
  );

  const begin = async () => {
    setPhase("preparing");
    track("screening_consent_given", { token });
    try {
      watcher.current = new IntegrityWatcher();
      if (videoRef.current) {
        // Camera must never block the assessment. getUserMedia can hang indefinitely
        // when the permission prompt is ignored — race it against a short timeout so
        // /join and /assessment/start always fire. Resolves → continue with camera;
        // rejects (ok=false) → camera_unavailable; neither within CAMERA_START_TIMEOUT_MS
        // → camera_timeout. In every case we proceed; the integrity snapshot records the
        // honest camera_permission ("granted" | "denied" | "unavailable").
        const CAMERA_START_TIMEOUT_MS = 6000;
        const started = watcher.current.start(videoRef.current);
        const outcome = await Promise.race([
          started.catch(() => false as const),
          new Promise<"timeout">((resolve) => setTimeout(() => resolve("timeout"), CAMERA_START_TIMEOUT_MS)),
        ]);
        if (outcome !== true) setCamDenied(true);
      }
      const joined = await api<{ campaign_id: string; sessions: JoinedSession[] }>(
        `/campaigns/public/${encodeURIComponent(token)}/join`,
        { json: {} },
      );
      track("screening_joined", { token, sessions: joined.sessions.length });
      const pending = joined.sessions;
      if (pending.length === 0) {
        setPhase("done");
        return;
      }
      setPlan(pending);
      setPlanIndex(0);
      await startCompetency(pending, 0);
    } catch (e) {
      fail(e);
    }
  };

  const submit = async () => {
    if (!session?.next_question || !answer.trim() || submitting) return;
    setSubmitting(true);
    const elapsed = Math.min(Math.max(Date.now() - questionShownAt.current, 0), 600000);
    try {
      const fb = await api<AnswerFeedback>("/assessment/answer", {
        json: {
          session_id: session.session_id,
          question_id: session.next_question.id,
          answer: answer.trim(),
          response_time_ms: elapsed,
        },
      });
      track("screening_question_answered", { token, n: fb.session.questions_answered });
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
      setSubmitting(false);
    }
  };

  const finishSession = async (sessionId: string) => {
    setPhase("switching");
    try {
      const flags = watcher.current?.snapshot();
      if (flags) {
        await api(`/assessment/${sessionId}/integrity`, { json: flags }).catch(() => undefined);
      }
      await api(`/assessment/complete/${sessionId}`, { method: "POST", json: {} });
      track("screening_competency_completed", { token, index: planIndex });
      const next = planIndex + 1;
      if (next < plan.length) {
        setPlanIndex(next);
        await startCompetency(plan, next);
      } else {
        watcher.current?.stop();
        track("screening_completed", { token });
        setPhase("done");
      }
    } catch (e) {
      fail(e);
    }
  };

  useEffect(() => {
    track("screening_runner_view", { token });
    return () => watcher.current?.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const q = session?.next_question ?? null;
  const qText = q ? (lang === "az" && q.question_az ? q.question_az : q.question_en) : "";
  const isMcq = Boolean(q?.options?.length);

  const progress = plan.length > 0 && phase !== "done" ? t.progress(planIndex + 1, plan.length) : undefined;
  const lowEnergy = energy === "low";

  return (
    <div className="min-h-screen bg-paper text-ink" data-energy={energy}>
      <ScreeningHeader
        lang={lang}
        setLang={setLang}
        energy={energy}
        setEnergy={setEnergy}
        progress={progress}
      />

      <main className={`mx-auto max-w-[640px] px-6 pb-20 ${lowEnergy ? "pt-8" : "pt-12"}`}>

      {/* Camera strip: small, visible, honest — candidate always sees what the camera sees */}
      <div className={phase === "consent" || phase === "done" ? "hidden" : "mb-6 flex items-center gap-3 rounded-[14px] border border-rule bg-paper-raised p-3"}>
        <video ref={videoRef} muted playsInline className="h-16 w-20 rounded-[10px] border border-rule object-cover" />
        <p className="text-xs leading-snug text-ink-faint">
          {camDenied ? t.camDenied : lang === "az" ? "Video yalnız brauzerinizdə işlənir." : "Video stays in your browser."}
        </p>
      </div>

      {phase === "consent" && (
        <div className="rounded-[18px] border border-rule bg-paper-raised p-6 shadow-[0_0_48px_rgba(124,92,252,0.08)]">
          <div className="mb-6 inline-flex rounded-full border border-seal/20 bg-seal-soft/40 px-3 py-1 text-xs font-semibold text-[#c4b5fd]">
            {t.tierLabel}
          </div>
          <h1 className="font-display text-[clamp(28px,5vw,40px)] font-bold leading-tight tracking-tight">
            {t.consentTitle}
          </h1>
          {!lowEnergy && <p className="mt-3 text-sm leading-relaxed text-ink-soft">{t.atlasHint}</p>}

          <div className="mt-6 space-y-3">
            <ConsentDisclosure title={lang === "az" ? "AI balı və insan qərarı" : "AI score and human decision"} body={t.consentBody} defaultOpen />
            <ConsentDisclosure title={lang === "az" ? "Kamera dürüstlük siqnalı" : "Camera integrity signal"} body={t.cameraBody} />
            <ConsentDisclosure title={lang === "az" ? "Hüquqlarınız" : "Your rights"} body={t.rightsBody} />
            {!lowEnergy && (
              <p className="rounded-[14px] border border-rule bg-paper-sunken px-4 py-3 text-[13px] leading-relaxed text-ink-faint">
                {t.tierBody}
              </p>
            )}
          </div>

          <button
            onClick={begin}
            className="mt-7 flex w-full items-center justify-center rounded-[14px] bg-seal px-8 py-[18px] font-display text-base font-bold tracking-tight text-white transition-shadow hover:shadow-[0_0_32px_rgba(124,92,252,0.35)]"
          >
            {t.agree}
          </button>
        </div>
      )}

      {(phase === "preparing" || phase === "switching") && (
        <div className="mt-8 space-y-3">
          <div className="h-6 w-2/5 animate-pulse rounded-md bg-paper-sunken" />
          <div className="h-24 animate-pulse rounded-xl bg-paper-sunken" />
          <p className="text-xs text-ink-faint">{phase === "preparing" ? t.preparing : t.switching}</p>
        </div>
      )}

      {phase === "question" && q && (
        <div className="mt-8">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-faint">
            {session?.competency_slug.replace(/_/g, " ")} · #{(session?.questions_answered ?? 0) + 1}
          </p>
          <h2 className="mt-3 font-display text-xl font-semibold leading-snug">{qText}</h2>

          {isMcq ? (
            <div className="mt-6 space-y-2">
              {q.options!.map((opt) => {
                const text = lang === "az" && opt.text_az ? opt.text_az : opt.text_en || opt.key;
                const selected = answer === opt.key;
                return (
                  <button
                    key={opt.key}
                    onClick={() => setAnswer(opt.key)}
                    className={`block w-full rounded-xl border px-4 py-3 text-left text-sm transition-colors ${
                      selected
                        ? "border-seal bg-seal-soft text-ink"
                        : "border-rule bg-paper-raised text-ink-soft hover:border-ink-faint"
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
              placeholder={t.open_placeholder}
              rows={6}
              maxLength={5000}
              className="mt-6 w-full rounded-xl border border-rule bg-paper-raised p-4 text-sm leading-relaxed text-ink outline-none focus:border-seal"
            />
          )}

          <button
            onClick={submit}
            disabled={!answer.trim() || submitting}
            className="mt-6 block w-full rounded-xl bg-seal px-6 py-3.5 text-center font-display text-sm font-semibold text-white transition-colors hover:bg-seal/90 disabled:opacity-40"
          >
            {submitting ? "…" : t.submit}
          </button>
        </div>
      )}

      {phase === "done" && (
        <div className="mt-8 rounded-xl border border-rule bg-paper-raised p-7">
          {/* Honest tier-2 badge: neutral violet, never the green "Verified Skills" treatment (§A.1) */}
          <div className="mb-5 inline-flex rounded-full border border-seal/20 bg-seal-soft/40 px-3 py-1 text-xs font-semibold text-[#c4b5fd]">
            {t.tierLabel}
          </div>
          <h1 className="font-display text-2xl font-bold tracking-tight">{t.doneTitle}</h1>
          <p className="mt-4 text-sm leading-relaxed text-ink-soft">{t.doneBody}</p>
          <p className="mt-4 rounded-[14px] border border-rule bg-paper-sunken px-4 py-3 text-[13px] leading-relaxed text-ink-faint">
            {t.tierBody}
          </p>
        </div>
      )}

      {phase === "error" && (
        <div className="mt-8 rounded-xl border border-rule bg-paper-raised p-7">
          <h1 className="font-display text-xl font-bold text-error">{t.error}</h1>
          <p className="mt-3 break-words text-sm text-ink-soft">{error}</p>
          <button
            onClick={() => {
              setError("");
              setPhase("consent");
            }}
            className="mt-6 rounded-xl border border-rule bg-paper-sunken px-5 py-2.5 text-sm text-ink-soft hover:border-seal"
          >
            {t.retry}
          </button>
        </div>
      )}
      </main>
    </div>
  );
}
