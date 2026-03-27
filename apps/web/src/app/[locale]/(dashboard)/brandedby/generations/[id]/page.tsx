"use client";

import { use, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import {
  Loader2,
  ArrowLeft,
  Download,
  Copy,
  Check,
  Share2,
  Clock,
  XCircle,
} from "lucide-react";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { useGeneration, useMyTwin } from "@/hooks/queries/use-brandedby";
import { cn } from "@/lib/utils/cn";

// ── LinkedIn icon (inline SVG — no dep) ──────────────────────────────────

function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

// ── TikTok icon ───────────────────────────────────────────────────────────

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.78 1.52V6.76a4.85 4.85 0 01-1.01-.07z" />
    </svg>
  );
}

// ── Share buttons for video ───────────────────────────────────────────────

interface VideoShareButtonsProps {
  videoUrl: string;
  displayName: string;
  genId: string;
}

function VideoShareButtons({ videoUrl, displayName, genId }: VideoShareButtonsProps) {
  const { t } = useTranslation();
  const [captionCopied, setCaptionCopied] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  const shareCaption = t("brandedby.shareCaption", {
    name: displayName,
    defaultValue: `My AI Twin just spoke for me. This is powered by my verified skills on Volaura. \n\n🚀 Try it at brandedby.xyz\n\n#BrandedBy #Volaura #AITwin #PersonalBrand`,
  });

  const brandedByUrl = `https://brandedby.xyz`;

  async function copyCaption() {
    try {
      await navigator.clipboard.writeText(shareCaption);
      setCaptionCopied(true);
      setTimeout(() => setCaptionCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(videoUrl);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  }

  function shareLinkedIn() {
    // LinkedIn post composer — share the BrandedBy page URL
    // (LinkedIn doesn't support direct MP4 upload via URL share)
    window.open(
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(brandedByUrl)}`,
      "_blank",
      "noopener,noreferrer",
    );
  }

  function downloadVideo() {
    // Trigger browser download
    const a = document.createElement("a");
    a.href = videoUrl;
    a.download = `brandedby-${genId.slice(0, 8)}.mp4`;
    a.target = "_blank";
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  return (
    <div className="space-y-4">
      {/* Caption to copy */}
      <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {t("brandedby.captionLabel", { defaultValue: "Caption (copy & paste)" })}
        </p>
        <p className="text-sm text-foreground whitespace-pre-line">{shareCaption}</p>
        <Button
          size="sm"
          variant="outline"
          onClick={copyCaption}
          className="gap-1.5"
        >
          {captionCopied ? (
            <>
              <Check className="size-3.5" aria-hidden="true" />
              {t("aura.copied", { defaultValue: "Copied!" })}
            </>
          ) : (
            <>
              <Copy className="size-3.5" aria-hidden="true" />
              {t("brandedby.copyCaption", { defaultValue: "Copy caption" })}
            </>
          )}
        </Button>
      </div>

      {/* Share + Download buttons */}
      <div className="flex flex-wrap gap-2">
        {/* LinkedIn */}
        <Button
          onClick={shareLinkedIn}
          className="gap-2 bg-[#0A66C2] hover:bg-[#0A66C2]/90 text-white"
          size="sm"
        >
          <LinkedInIcon className="size-4" />
          LinkedIn
        </Button>

        {/* TikTok — download + paste caption */}
        <Button
          onClick={downloadVideo}
          variant="outline"
          className="gap-2 border-zinc-800 text-foreground hover:bg-zinc-900/5"
          size="sm"
        >
          <TikTokIcon className="size-4" />
          {t("brandedby.downloadForTikTok", { defaultValue: "Download for TikTok" })}
        </Button>

        {/* Download MP4 */}
        <Button
          onClick={downloadVideo}
          variant="outline"
          size="sm"
          className="gap-1.5"
        >
          <Download className="size-3.5" aria-hidden="true" />
          {t("brandedby.downloadMp4", { defaultValue: "Download MP4" })}
        </Button>

        {/* Copy video link */}
        <Button
          onClick={copyLink}
          variant="outline"
          size="sm"
          className="gap-1.5"
        >
          {linkCopied ? (
            <>
              <Check className="size-3.5" aria-hidden="true" />
              {t("aura.copied", { defaultValue: "Copied!" })}
            </>
          ) : (
            <>
              <Copy className="size-3.5" aria-hidden="true" />
              {t("brandedby.copyLink", { defaultValue: "Copy video link" })}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function GenerationPage({
  params,
}: {
  params: Promise<{ id: string; locale: string }>;
}) {
  const { id: genId, locale } = use(params);
  const { t } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const { data: gen, isLoading, error } = useGeneration(genId);
  const { data: twin } = useMyTwin();

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [error, locale, router]);

  // ── Loading ──

  if (isLoading) {
    return (
      <>
        <TopBar title={t("brandedby.videoTitle", { defaultValue: "Your Video" })} />
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="size-8 animate-spin text-primary" aria-label={t("common.loading")} />
        </div>
      </>
    );
  }

  // ── Error ──

  if (error || !gen) {
    return (
      <>
        <TopBar title={t("brandedby.videoTitle", { defaultValue: "Your Video" })} />
        <div className="flex flex-col items-center justify-center h-64 gap-3 text-center p-6">
          <XCircle className="size-8 text-destructive" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">
            {t("error.generic", { defaultValue: "Something went wrong" })}
          </p>
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="size-4 mr-1.5" aria-hidden="true" />
            {t("common.back", { defaultValue: "Back" })}
          </Button>
        </div>
      </>
    );
  }

  // ── Processing / Queued ──

  if (gen.status === "queued" || gen.status === "processing") {
    return (
      <>
        <TopBar title={t("brandedby.videoTitle", { defaultValue: "Your Video" })} />
        <div className="mx-auto max-w-lg p-6 space-y-6">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 -ml-1"
            onClick={() => router.push(`/${locale}/brandedby`)}
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("brandedby.back", { defaultValue: "Back to AI Twin" })}
          </Button>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center gap-6 py-12 text-center"
          >
            <div className="size-16 rounded-full bg-blue-500/10 flex items-center justify-center">
              {gen.status === "processing" ? (
                <Loader2 className="size-8 text-blue-500 animate-spin" aria-hidden="true" />
              ) : (
                <Clock className="size-8 text-yellow-500" aria-hidden="true" />
              )}
            </div>
            <div>
              <h2 className="text-xl font-semibold">
                {gen.status === "processing"
                  ? t("brandedby.generating", { defaultValue: "Generating your video…" })
                  : t("brandedby.inQueue", { defaultValue: "In queue — hang tight" })}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {t("brandedby.generatingHint", {
                  defaultValue: "This usually takes 1–3 minutes. This page refreshes automatically.",
                })}
              </p>
            </div>
            <div className="w-full max-w-xs bg-muted rounded-full h-1.5 overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                animate={{ width: gen.status === "processing" ? "75%" : "30%" }}
                transition={{ duration: 1, ease: "easeInOut" }}
              />
            </div>
          </motion.div>
        </div>
      </>
    );
  }

  // ── Failed ──

  if (gen.status === "failed") {
    return (
      <>
        <TopBar title={t("brandedby.videoTitle", { defaultValue: "Your Video" })} />
        <div className="mx-auto max-w-lg p-6 space-y-4">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 -ml-1"
            onClick={() => router.push(`/${locale}/brandedby`)}
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("brandedby.back", { defaultValue: "Back to AI Twin" })}
          </Button>
          <div className="flex flex-col items-center gap-4 py-10 text-center">
            <XCircle className="size-10 text-destructive" aria-hidden="true" />
            <div>
              <h2 className="text-lg font-semibold">{t("brandedby.failed", { defaultValue: "Generation failed" })}</h2>
              {gen.error_message && (
                <p className="text-sm text-muted-foreground mt-1">{gen.error_message}</p>
              )}
            </div>
            <Button onClick={() => router.push(`/${locale}/brandedby`)}>
              {t("brandedby.tryAgain", { defaultValue: "Try again" })}
            </Button>
          </div>
        </div>
      </>
    );
  }

  // ── Completed — The $730K screen ──

  const videoUrl = gen.output_url ?? "";

  return (
    <>
      <TopBar title={t("brandedby.videoTitle", { defaultValue: "Your Video" })} />
      <div className="mx-auto max-w-lg p-6 space-y-6">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 -ml-1"
          onClick={() => router.push(`/${locale}/brandedby`)}
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          {t("brandedby.back", { defaultValue: "Back to AI Twin" })}
        </Button>

        {/* Video player */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="rounded-2xl overflow-hidden border border-border bg-black shadow-xl"
        >
          <video
            src={videoUrl}
            controls
            autoPlay
            loop
            playsInline
            className="w-full aspect-video object-contain"
            aria-label={t("brandedby.videoAlt", { defaultValue: "AI Twin video" })}
          />
        </motion.div>

        {/* CTA headline */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-center"
        >
          <h2 className="text-lg font-bold flex items-center justify-center gap-2">
            <Share2 className="size-5 text-primary" aria-hidden="true" />
            {t("brandedby.shareTitle", { defaultValue: "Share to grow your personal brand" })}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            {t("brandedby.shareHint", {
              defaultValue: "Post this on LinkedIn & TikTok. Add the caption below to attract opportunities.",
            })}
          </p>
        </motion.div>

        {/* Share buttons */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <VideoShareButtons
            videoUrl={videoUrl}
            displayName={twin?.display_name ?? ""}
            genId={genId}
          />
        </motion.div>

        {/* Script */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="rounded-xl border border-border bg-muted/30 p-4 space-y-1"
        >
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {t("brandedby.scriptLabel", { defaultValue: "Script" })}
          </p>
          <p className="text-sm text-foreground leading-relaxed">{gen.input_text}</p>
        </motion.div>
      </div>
    </>
  );
}
