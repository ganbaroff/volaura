"use client";

import { useMemo, useState } from "react";
import { notFound, useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { ArrowRight, RefreshCw, Sparkles, Wand2 } from "lucide-react";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCreateGeneration,
  useCreateTwin,
  useGenerations,
  useMyTwin,
  type Generation,
} from "@/hooks/queries/use-brandedby";

const BRANDEDBY_ENABLED = process.env.NEXT_PUBLIC_ENABLE_BRANDEDBY === "true";

function statusTone(status: Generation["status"]) {
  switch (status) {
    case "completed":
      return "text-green-400";
    case "failed":
      return "text-red-400";
    case "processing":
      return "text-amber-400";
    default:
      return "text-muted-foreground";
  }
}

function statusLabel(status: Generation["status"]) {
  switch (status) {
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "processing":
      return "Processing";
    default:
      return "Queued";
  }
}

function GenerationSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-24" />
      </div>
    </div>
  );
}

export default function BrandedByPage() {
  if (!BRANDEDBY_ENABLED) {
    notFound();
  }

  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();

  const { data: twin, isLoading: twinLoading, error: twinError, refetch: refetchTwin } = useMyTwin();
  const {
    data: generations,
    isLoading: generationsLoading,
    error: generationsError,
    refetch: refetchGenerations,
  } = useGenerations(20);
  const createTwin = useCreateTwin();
  const createGeneration = useCreateGeneration();

  const [displayName, setDisplayName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [genType, setGenType] = useState<"text_chat" | "audio" | "video">("text_chat");

  const sortedGenerations = useMemo(
    () => [...(generations ?? [])].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)),
    [generations]
  );

  const loading = twinLoading || generationsLoading;
  const error = twinError ?? generationsError;

  async function handleCreateTwin() {
    const name = displayName.trim();
    if (!name) return;
    await createTwin.mutateAsync({ display_name: name });
    setDisplayName("");
    refetchTwin();
  }

  async function handleCreateGeneration() {
    if (!twin) return;
    const input = prompt.trim();
    if (!input) return;
    const generation = await createGeneration.mutateAsync({
      twin_id: twin.id,
      gen_type: genType,
      input_text: input,
    });
    setPrompt("");
    router.push(`/${locale}/brandedby/generations/${generation.id}`);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 space-y-6">
      <TopBar title={t("nav.brandedby", { defaultValue: "BrandedBy" })} />

      <section className="rounded-3xl border border-border bg-card p-5 space-y-4">
        <div className="space-y-1">
          <p className="text-sm font-medium text-primary">BrandedBy</p>
          <h1 className="text-2xl font-semibold text-foreground">
            {t("brandedby.title", { defaultValue: "Your AI twin workspace" })}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("brandedby.subtitle", {
              defaultValue: "Create a twin, launch a generation, and track its status in one place.",
            })}
          </p>
        </div>

        {!twin && !loading && !error && (
          <div className="rounded-2xl border border-dashed border-border bg-surface-container-low p-4 space-y-4">
            <div className="space-y-1">
              <p className="text-sm font-semibold text-foreground">
                {t("brandedby.noTwinTitle", { defaultValue: "Create your AI twin first" })}
              </p>
              <p className="text-sm text-muted-foreground">
                {t("brandedby.noTwinBody", {
                  defaultValue: "BrandedBy already has the backend and generation pipeline. This page now wires it up.",
                })}
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t("brandedby.twinNamePlaceholder", { defaultValue: "Twin display name" })}
                className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <Button
                onClick={handleCreateTwin}
                disabled={!displayName.trim() || createTwin.isPending}
                className="gap-2"
              >
                <Sparkles className="size-4" />
                {createTwin.isPending
                  ? t("common.loading", { defaultValue: "Loading" })
                  : t("brandedby.createTwin", { defaultValue: "Create twin" })}
              </Button>
            </div>
          </div>
        )}

        {twin && (
          <div className="rounded-2xl border border-border bg-surface-container-low p-4 space-y-4">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">{twin.display_name}</p>
                <p className="text-sm text-muted-foreground">
                  {twin.tagline || t("brandedby.twinReady", { defaultValue: "Twin ready for new generations." })}
                </p>
              </div>
              <span className="text-xs uppercase tracking-wide text-muted-foreground">
                {twin.status}
              </span>
            </div>

            <div className="space-y-3">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                placeholder={t("brandedby.promptPlaceholder", {
                  defaultValue: "Describe the generation you want your twin to create.",
                })}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <select
                  value={genType}
                  onChange={(e) => setGenType(e.target.value as "text_chat" | "audio" | "video")}
                  className="flex h-10 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="text_chat">Text chat</option>
                  <option value="audio">Audio</option>
                  <option value="video">Video</option>
                </select>
                <Button
                  onClick={handleCreateGeneration}
                  disabled={!prompt.trim() || createGeneration.isPending}
                  className="gap-2"
                >
                  <Wand2 className="size-4" />
                  {createGeneration.isPending
                    ? t("common.loading", { defaultValue: "Loading" })
                    : t("brandedby.createGeneration", { defaultValue: "Create generation" })}
                </Button>
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              {t("brandedby.generationsTitle", { defaultValue: "Recent generations" })}
            </h2>
            <p className="text-sm text-muted-foreground">
              {t("brandedby.generationsSubtitle", {
                defaultValue: "Track queue state, processing, failures, and completed output.",
              })}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchTwin();
              refetchGenerations();
            }}
            className="gap-2"
          >
            <RefreshCw className="size-4" />
            {t("common.refresh", { defaultValue: "Refresh" })}
          </Button>
        </div>

        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <GenerationSkeleton key={i} />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-4 space-y-3">
            <p className="text-sm font-semibold text-foreground">
              {t("brandedby.errorTitle", { defaultValue: "We couldn't load BrandedBy right now." })}
            </p>
            <p className="text-sm text-muted-foreground">
              {t("brandedby.errorBody", {
                defaultValue: "The page is wired, but this request failed. Retry without leaving the flow.",
              })}
            </p>
            <Button
              variant="outline"
              onClick={() => {
                refetchTwin();
                refetchGenerations();
              }}
            >
              {t("error.retry", { defaultValue: "Retry" })}
            </Button>
          </div>
        )}

        {!loading && !error && sortedGenerations.length === 0 && (
          <div className="rounded-2xl border border-dashed border-border bg-card p-6 text-center space-y-3">
            <p className="text-sm font-semibold text-foreground">
              {t("brandedby.emptyTitle", { defaultValue: "No generations yet" })}
            </p>
            <p className="text-sm text-muted-foreground">
              {t("brandedby.emptyBody", {
                defaultValue: "Your next generation will show up here with live queue and processing status.",
              })}
            </p>
            <Button
              onClick={() => {
                const area = document.querySelector("textarea");
                if (area instanceof HTMLTextAreaElement) area.focus();
              }}
              disabled={!twin}
              className="gap-2"
            >
              <Sparkles className="size-4" />
              {t("brandedby.emptyCta", { defaultValue: "Start a generation" })}
            </Button>
          </div>
        )}

        {!loading && !error && sortedGenerations.length > 0 && (
          <div className="space-y-3">
            {sortedGenerations.map((generation) => (
              <button
                key={generation.id}
                type="button"
                onClick={() => router.push(`/${locale}/brandedby/generations/${generation.id}`)}
                className="w-full rounded-2xl border border-border bg-card p-4 text-left transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground capitalize">
                      {generation.gen_type.replace("_", " ")}
                    </p>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {generation.input_text}
                    </p>
                  </div>
                  <span className={`text-xs font-medium uppercase tracking-wide ${statusTone(generation.status)}`}>
                    {statusLabel(generation.status)}
                  </span>
                </div>
                <div className="mt-3 flex items-center justify-between gap-3 text-xs text-muted-foreground">
                  <span>
                    {generation.queue_position != null
                      ? `Queue #${generation.queue_position}`
                      : generation.completed_at
                      ? new Date(generation.completed_at).toLocaleString()
                      : new Date(generation.created_at).toLocaleString()}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    {generation.crystal_cost} crystals
                    <ArrowRight className="size-3" />
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
