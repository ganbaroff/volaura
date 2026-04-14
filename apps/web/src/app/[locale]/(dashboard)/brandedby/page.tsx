"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Loader2, Sparkles, Video, Clock, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  useMyTwin,
  useGenerations,
  useCreateTwin,
  useRefreshPersonality,
  useActivateTwin,
  useCreateGeneration,
} from "@/hooks/queries/use-brandedby";
import type { Generation } from "@/hooks/queries/use-brandedby";
import { cn } from "@/lib/utils/cn";

// ── Generation status badge ───────────────────────────────────────────────

function StatusBadge({ status }: { status: Generation["status"] }) {
  const { t } = useTranslation();

  const config: Record<Generation["status"], { label: string; className: string; icon: React.ReactNode }> = {
    queued: {
      label: t("brandedby.status.queued", { defaultValue: "In queue" }),
      className: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
      icon: <Clock className="size-3" aria-hidden="true" />,
    },
    processing: {
      label: t("brandedby.status.processing", { defaultValue: "Generating…" }),
      className: "bg-blue-500/10 text-blue-600 border-blue-500/20",
      icon: <Loader2 className="size-3 animate-spin" aria-hidden="true" />,
    },
    completed: {
      label: t("brandedby.status.completed", { defaultValue: "Ready" }),
      className: "bg-green-500/10 text-green-600 border-green-500/20",
      icon: <CheckCircle className="size-3" aria-hidden="true" />,
    },
    failed: {
      label: t("brandedby.status.failed", { defaultValue: "Failed" }),
      className: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      icon: <XCircle className="size-3" aria-hidden="true" />,
    },
  };

  const { label, className, icon } = config[status];

  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium", className)}>
      {icon}
      {label}
    </span>
  );
}

// ── Generation card ───────────────────────────────────────────────────────

function GenerationCard({ gen, locale }: { gen: Generation; locale: string }) {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <div className="flex items-start gap-3 p-4 rounded-xl border border-border bg-card hover:bg-muted/30 transition-colors">
      <div className="size-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
        <Video className="size-5 text-primary" aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{gen.input_text}</p>
        <div className="flex items-center gap-2 mt-1">
          <StatusBadge status={gen.status} />
          <span className="text-xs text-muted-foreground">
            {new Date(gen.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
      {gen.status === "completed" && gen.output_url && (
        <Button
          size="sm"
          variant="outline"
          className="shrink-0"
          onClick={() => router.push(`/${locale}/brandedby/generations/${gen.id}`)}
        >
          {t("brandedby.view", { defaultValue: "View & Share" })}
        </Button>
      )}
    </div>
  );
}

// ── New generation form ───────────────────────────────────────────────────

function NewGenerationForm({ twinId }: { twinId: string }) {
  const { t } = useTranslation();
  const [script, setScript] = useState("");
  const [skipQueue, setSkipQueue] = useState(false);
  const { mutate: createGeneration, isPending, error } = useCreateGeneration();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (script.trim().length < 10) return;
    createGeneration({
      twin_id: twinId,
      gen_type: "video",
      input_text: script.trim(),
      skip_queue: skipQueue,
    });
    setScript("");
    setSkipQueue(false);
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <textarea
        value={script}
        onChange={(e) => setScript(e.target.value)}
        placeholder={t("brandedby.scriptPlaceholder", {
          defaultValue: "Write what your AI Twin will say… (e.g. 'Hi, I'm Yusif. I'm a professional from Baku…')",
        })}
        rows={4}
        maxLength={2000}
        className={cn(
          "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm",
          "placeholder:text-muted-foreground resize-none focus-visible:outline-none",
          "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        )}
        aria-label={t("brandedby.scriptLabel", { defaultValue: "AI Twin script" })}
      />
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
          <input
            type="checkbox"
            checked={skipQueue}
            onChange={(e) => setSkipQueue(e.target.checked)}
            className="rounded border-input"
          />
          {t("brandedby.skipQueue", { defaultValue: "Skip queue (25 crystals)" })}
        </label>
        <Button
          type="submit"
          disabled={isPending || script.trim().length < 10}
          className="gap-1.5"
        >
          {isPending ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              {t("common.loading", { defaultValue: "Generating…" })}
            </>
          ) : (
            <>
              <Sparkles className="size-4" aria-hidden="true" />
              {t("brandedby.generate", { defaultValue: "Generate Video" })}
            </>
          )}
        </Button>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">{t("error.generic", { defaultValue: "Something went wrong. Please try again." })}</p>
      )}
    </form>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function BrandedByPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const router = useRouter();
  const isMounted = useRef(true);
  const [isCreatingTwin, setIsCreatingTwin] = useState(false);
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const { data: twin, isLoading: twinLoading, error: twinError, refetch: refetchTwin } = useMyTwin();
  const { data: generations, isLoading: gensLoading } = useGenerations();
  const { mutate: createTwin, isPending: isCreating } = useCreateTwin();
  const { mutate: refreshPersonality, isPending: isRefreshing } = useRefreshPersonality();
  const { mutate: activateTwin, isPending: isActivating } = useActivateTwin();

  useEffect(() => {
    if (twinError instanceof ApiError && twinError.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [twinError, locale, router]);

  // ── Loading ──

  if (twinLoading) {
    return (
      <>
        <TopBar title="BrandedBy" />
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="size-8 animate-spin text-primary" aria-label={t("common.loading")} />
        </div>
      </>
    );
  }

  // ── No twin yet — setup flow ──

  if (!twin) {
    return (
      <>
        <TopBar title="BrandedBy" />
        <div className="mx-auto max-w-lg p-6 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center space-y-3 py-8"
          >
            <div className="size-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
              <Sparkles className="size-8 text-primary" aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-bold">
              {t("brandedby.createTitle", { defaultValue: "Create your AI Twin" })}
            </h2>
            <p className="text-muted-foreground text-sm max-w-xs mx-auto">
              {t("brandedby.createSubtitle", {
                defaultValue: "Your verified skills power a talking-head video. Share it on LinkedIn and TikTok.",
              })}
            </p>
          </motion.div>

          {!isCreatingTwin ? (
            <Button
              onClick={() => setIsCreatingTwin(true)}
              className="w-full gap-2"
              size="lg"
            >
              <Sparkles className="size-4" aria-hidden="true" />
              {t("brandedby.getStarted", { defaultValue: "Get Started" })}
            </Button>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t("brandedby.displayNamePlaceholder", { defaultValue: "Your name (e.g. Yusif Ganbarov)" })}
                maxLength={100}
                className={cn(
                  "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm",
                  "placeholder:text-muted-foreground focus-visible:outline-none",
                  "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                )}
              />
              <Button
                onClick={() => {
                  if (displayName.trim().length < 2) return;
                  createTwin({ display_name: displayName.trim() });
                }}
                disabled={isCreating || displayName.trim().length < 2}
                className="w-full gap-2"
              >
                {isCreating ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Sparkles className="size-4" aria-hidden="true" />
                )}
                {t("brandedby.createBtn", { defaultValue: "Create AI Twin" })}
              </Button>
            </motion.div>
          )}
        </div>
      </>
    );
  }

  // ── Twin exists — show status + generate form ──

  const isActive = twin.status === "active";
  const canActivate = twin.status === "draft" && !!twin.photo_url && !!twin.personality_prompt;

  return (
    <>
      <TopBar title="BrandedBy" />
      <div className="mx-auto max-w-2xl p-6 space-y-6">

        {/* Twin header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-border bg-card p-5 flex items-center gap-4"
        >
          {twin.photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element -- BrandedBy twin photo may come from fal.ai or other AI provider CDNs outside remotePatterns
            <img
              src={twin.photo_url}
              alt={twin.display_name}
              className="size-16 rounded-full object-cover shrink-0"
            />
          ) : (
            <div className="size-16 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <Sparkles className="size-7 text-primary" aria-hidden="true" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold">{twin.display_name}</h2>
            {twin.tagline && (
              <p className="text-sm text-muted-foreground truncate">{twin.tagline}</p>
            )}
            <span className={cn(
              "mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium",
              isActive
                ? "bg-green-500/10 text-green-600 border-green-500/20"
                : "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
            )}>
              {isActive
                ? t("brandedby.active", { defaultValue: "Active" })
                : t("brandedby.draft", { defaultValue: "Draft" })}
            </span>
          </div>
        </motion.div>

        {/* Setup steps (only shown while draft) */}
        {!isActive && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-xl border border-border bg-card p-5 space-y-4"
          >
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              {t("brandedby.setupTitle", { defaultValue: "Setup" })}
            </h3>

            {/* Step 1: Photo */}
            <SetupStep
              done={!!twin.photo_url}
              number={1}
              label={t("brandedby.step1", { defaultValue: "Upload portrait photo" })}
            />

            {/* Step 2: Generate personality */}
            <SetupStep
              done={!!twin.personality_prompt}
              number={2}
              label={t("brandedby.step2", { defaultValue: "Generate AI personality from your AURA" })}
              action={
                !twin.personality_prompt && twin.id ? (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isRefreshing}
                    onClick={() => refreshPersonality(twin.id)}
                    className="gap-1"
                  >
                    {isRefreshing ? (
                      <Loader2 className="size-3 animate-spin" aria-hidden="true" />
                    ) : (
                      <RefreshCw className="size-3" aria-hidden="true" />
                    )}
                    {t("brandedby.generate", { defaultValue: "Generate" })}
                  </Button>
                ) : null
              }
            />

            {/* Step 3: Activate */}
            <SetupStep
              done={false}
              number={3}
              label={t("brandedby.step3", { defaultValue: "Activate AI Twin" })}
              action={
                canActivate ? (
                  <Button
                    size="sm"
                    disabled={isActivating}
                    onClick={() => activateTwin(twin.id)}
                    className="gap-1"
                  >
                    {isActivating && <Loader2 className="size-3 animate-spin" aria-hidden="true" />}
                    {t("brandedby.activate", { defaultValue: "Activate" })}
                  </Button>
                ) : null
              }
            />
          </motion.div>
        )}

        {/* Video generation form (only when active) */}
        {isActive && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="rounded-xl border border-border bg-card p-5 space-y-4"
          >
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              {t("brandedby.newVideo", { defaultValue: "New Video" })}
            </h3>
            <NewGenerationForm twinId={twin.id} />
          </motion.div>
        )}

        {/* Generations list */}
        {generations && generations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-3"
          >
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              {t("brandedby.recentVideos", { defaultValue: "Recent Videos" })}
            </h3>
            {gensLoading ? (
              <Loader2 className="size-5 animate-spin text-muted-foreground" aria-hidden="true" />
            ) : (
              generations.map((gen) => (
                <GenerationCard key={gen.id} gen={gen} locale={locale} />
              ))
            )}
          </motion.div>
        )}

        {/* Empty state */}
        {isActive && (!generations || generations.length === 0) && !gensLoading && (
          <div className="text-center py-8 text-sm text-muted-foreground">
            {t("brandedby.noVideosYet", { defaultValue: "No videos yet. Generate your first one above." })}
          </div>
        )}
      </div>
    </>
  );
}

// ── Setup step component ──────────────────────────────────────────────────

function SetupStep({
  number,
  label,
  done,
  action,
}: {
  number: number;
  label: string;
  done: boolean;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className={cn(
        "size-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
        done
          ? "bg-green-500/15 text-green-600"
          : "bg-muted text-muted-foreground",
      )}>
        {done ? <CheckCircle className="size-4" aria-hidden="true" /> : number}
      </div>
      <span className={cn("text-sm flex-1", done && "line-through text-muted-foreground")}>
        {label}
      </span>
      {!done && action}
    </div>
  );
}
