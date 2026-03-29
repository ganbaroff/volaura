"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import { BadgeCheck, AlertCircle, Clock, CheckCircle2, ExternalLink } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils/cn";
import { API_BASE } from "@/lib/api/client";

/* ─── Types ─── */
type TokenState = "loading" | "valid" | "invalid" | "expired" | "used";
type FlowStep = "intro" | "rating" | "comment" | "submitting" | "success";

interface VolunteerInfo {
  volunteer_display_name: string;
  volunteer_username: string;
  volunteer_avatar_url: string | null;
  verifier_name: string;
  verifier_org: string | null;
  competency_id: string;
}

/* ─── Constants ─── */
const API_URL = API_BASE;

const COMPETENCY_LABELS: Record<string, { en: string; az: string }> = {
  communication:        { en: "Communication",       az: "Kommunikasiya" },
  reliability:          { en: "Reliability",          az: "Etibarlılıq" },
  english_proficiency:  { en: "English Proficiency",  az: "İngilis dili" },
  leadership:           { en: "Leadership",            az: "Liderlik" },
  event_performance:    { en: "Event Performance",     az: "Tədbir performansı" },
  tech_literacy:        { en: "Tech Literacy",         az: "Texniki savadlılıq" },
  adaptability:         { en: "Adaptability",          az: "Uyğunlaşma" },
  empathy_safeguarding: { en: "Empathy & Safeguarding",az: "Empatiya və müdafiə" },
};

const RATING_OPTIONS = [
  { value: 1, emoji: "😕", label: "verify.ratingPoor" },
  { value: 2, emoji: "😐", label: "verify.ratingFair" },
  { value: 3, emoji: "🙂", label: "verify.ratingGood" },
  { value: 4, emoji: "😊", label: "verify.ratingGreat" },
  { value: 5, emoji: "🔥", label: "verify.ratingExceptional" },
] as const;

/* ─── Helper: Avatar initials ─── */
function Initials({ name }: { name: string }) {
  const parts = name.trim().split(" ");
  const letters =
    parts.length >= 2
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`
      : name.slice(0, 2);
  return <>{letters.toUpperCase()}</>;
}

/* ─── Token Error Screen ─── */
function ErrorScreen({
  state,
  t,
}: {
  state: "invalid" | "expired" | "used";
  t: (k: string) => string;
}) {
  const configs = {
    invalid: {
      icon: AlertCircle,
      iconClass: "text-red-400",
      title: t("verify.errorInvalidTitle"),
      body: t("verify.errorInvalidBody"),
    },
    expired: {
      icon: Clock,
      iconClass: "text-amber-400",
      title: t("verify.errorExpiredTitle"),
      body: t("verify.errorExpiredBody"),
    },
    used: {
      icon: CheckCircle2,
      iconClass: "text-green-400",
      title: t("verify.errorUsedTitle"),
      body: t("verify.errorUsedBody"),
    },
  };

  const { icon: Icon, iconClass, title, body } = configs[state];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col items-center text-center gap-4 py-8"
    >
      <span className={cn("size-16 rounded-full bg-white/6 flex items-center justify-center", iconClass)}>
        <Icon className="size-8" aria-hidden="true" />
      </span>
      <div className="space-y-1">
        <h2 className="text-lg font-bold text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">{body}</p>
      </div>
    </motion.div>
  );
}

/* ─── Intro Screen ─── */
function IntroScreen({
  info,
  locale,
  onStart,
  t,
}: {
  info: VolunteerInfo;
  locale: string;
  onStart: () => void;
  t: (k: string, opts?: Record<string, string>) => string;
}) {
  const competencyLabel =
    COMPETENCY_LABELS[info.competency_id]?.[locale === "az" ? "az" : "en"] ??
    info.competency_id;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-6"
    >
      {/* Volunteer card */}
      <div className="flex flex-col items-center gap-3 py-4">
        <div className="size-20 rounded-full bg-primary/20 flex items-center justify-center text-2xl font-bold text-primary">
          {info.volunteer_avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={info.volunteer_avatar_url}
              alt={info.volunteer_display_name}
              className="size-full rounded-full object-cover"
            />
          ) : (
            <Initials name={info.volunteer_display_name} />
          )}
        </div>
        <div className="text-center">
          <h2 className="text-xl font-bold text-foreground">{info.volunteer_display_name}</h2>
          <p className="text-sm text-muted-foreground">@{info.volunteer_username}</p>
        </div>
      </div>

      {/* What you're rating */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-2 text-center">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {t("verify.youAreRating")}
        </p>
        <p className="text-lg font-bold text-primary">{competencyLabel}</p>
        <p className="text-xs text-muted-foreground">
          {t("verify.requestedBy", { name: info.verifier_name })}
          {info.verifier_org ? ` · ${info.verifier_org}` : ""}
        </p>
      </div>

      {/* Estimate + CTA */}
      <div className="space-y-3">
        <p className="text-center text-sm text-muted-foreground">{t("verify.timeEstimate")}</p>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onStart}
          className="w-full rounded-xl bg-primary py-3.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {t("verify.startRating")} →
        </motion.button>
      </div>
    </motion.div>
  );
}

/* ─── Rating Screen ─── */
function RatingScreen({
  info,
  locale,
  onSelect,
  t,
}: {
  info: VolunteerInfo;
  locale: string;
  onSelect: (rating: number) => void;
  t: (k: string) => string;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const competencyLabel =
    COMPETENCY_LABELS[info.competency_id]?.[locale === "az" ? "az" : "en"] ??
    info.competency_id;

  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.28 }}
      className="space-y-6"
    >
      <div className="text-center space-y-1">
        <h2 className="text-lg font-bold text-foreground">
          {t("verify.ratingQuestion")}
        </h2>
        <p className="text-sm font-semibold text-primary">{competencyLabel}</p>
        <p className="text-sm text-muted-foreground">
          {info.volunteer_display_name}
        </p>
      </div>

      {/* Emoji buttons */}
      <div
        role="group"
        aria-label={t("verify.ratingQuestion")}
        className="flex justify-center gap-3"
      >
        {RATING_OPTIONS.map(({ value, emoji, label }) => (
          <motion.button
            key={value}
            whileHover={{ scale: 1.15, y: -4 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onSelect(value)}
            onMouseEnter={() => setHovered(value)}
            onMouseLeave={() => setHovered(null)}
            aria-label={`${t(label)} (${value}/5)`}
            className="flex flex-col items-center gap-1.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-xl p-2"
          >
            <span
              className={cn(
                "text-4xl transition-all duration-150",
                hovered !== null && hovered !== value && "opacity-30 scale-90"
              )}
            >
              {emoji}
            </span>
            <span
              className={cn(
                "text-[10px] font-medium transition-colors",
                hovered === value ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {t(label)}
            </span>
          </motion.button>
        ))}
      </div>

      <p className="text-center text-xs text-muted-foreground">{t("verify.tapToRate")}</p>
    </motion.div>
  );
}

/* ─── Comment Screen ─── */
function CommentScreen({
  rating,
  onSubmit,
  submitting,
  t,
}: {
  rating: number;
  onSubmit: (comment: string | null) => void;
  submitting: boolean;
  t: (k: string) => string;
}) {
  const [comment, setComment] = useState("");
  const selected = RATING_OPTIONS.find((r) => r.value === rating);

  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.28 }}
      className="space-y-5"
    >
      {/* Selected rating summary */}
      <div className="flex items-center justify-center gap-3 py-2">
        <span className="text-4xl">{selected?.emoji}</span>
        <div>
          <p className="text-sm font-semibold text-foreground">{t(selected?.label ?? "")}</p>
          <p className="text-xs text-muted-foreground">{rating}/5</p>
        </div>
      </div>

      {/* Optional comment */}
      <div className="space-y-2">
        <label htmlFor="verify-comment" className="text-sm font-medium text-foreground">
          {t("verify.commentLabel")}
        </label>
        <textarea
          id="verify-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value.slice(0, 500))}
          rows={4}
          placeholder={t("verify.commentPlaceholder")}
          className="w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:ring-2 focus:ring-ring resize-none"
          aria-describedby="comment-count"
        />
        <p
          id="comment-count"
          className="text-right text-xs text-muted-foreground"
          aria-live="polite"
        >
          {comment.length}/500
        </p>
      </div>

      <div className="flex gap-2.5">
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSubmit(null)}
          disabled={submitting}
          className="flex-1 rounded-xl border border-border bg-card py-3 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors disabled:opacity-50"
        >
          {t("verify.skipComment")}
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSubmit(comment.trim() || null)}
          disabled={submitting}
          className="flex-1 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {submitting ? t("verify.submitting") : t("verify.submit")}
        </motion.button>
      </div>
    </motion.div>
  );
}

/* ─── Success Screen ─── */
function SuccessScreen({
  info,
  rating,
  locale,
  t,
}: {
  info: VolunteerInfo;
  rating: number;
  locale: string;
  t: (k: string, opts?: Record<string, string>) => string;
}) {
  const selected = RATING_OPTIONS.find((r) => r.value === rating);
  const competencyLabel =
    COMPETENCY_LABELS[info.competency_id]?.[locale === "az" ? "az" : "en"] ??
    info.competency_id;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, type: "spring", stiffness: 180, damping: 18 }}
      className="flex flex-col items-center gap-5 py-6 text-center"
    >
      {/* Celebration */}
      <motion.div
        animate={{ rotate: [0, -8, 8, -4, 4, 0] }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="text-6xl"
        aria-hidden="true"
      >
        {selected?.emoji ?? "🎉"}
      </motion.div>

      <div className="space-y-2">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <BadgeCheck className="size-7 text-green-400 mx-auto mb-2" aria-hidden="true" />
          <h2 className="text-xl font-bold text-foreground">{t("verify.successTitle")}</h2>
        </motion.div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.45 }}
          className="text-sm text-muted-foreground leading-relaxed max-w-xs mx-auto"
        >
          {t("verify.successBody", { name: info.volunteer_display_name, competency: competencyLabel })}
        </motion.p>
      </div>

      {/* Card summary */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="w-full rounded-xl border border-green-400/20 bg-green-500/5 p-4 space-y-1"
      >
        <p className="text-xs text-muted-foreground uppercase tracking-wide">{t("verify.yourRating")}</p>
        <p className="text-2xl font-black text-foreground">{selected?.emoji} {t(selected?.label ?? "")}</p>
        <p className="text-xs text-muted-foreground">{competencyLabel} · {rating}/5</p>
      </motion.div>

      {/* Link to Volaura */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
      >
        <Link
          href={`/${locale}`}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {t("verify.learnAboutVolaura")}
          <ExternalLink className="size-3" aria-hidden="true" />
        </Link>
      </motion.div>
    </motion.div>
  );
}

/* ─── Main Page ─── */
export default function VerifyPage() {
  const { token, locale } = useParams<{ token: string; locale: string }>();
  const { t } = useTranslation();

  const [tokenState, setTokenState] = useState<TokenState>("loading");
  const [info, setInfo] = useState<VolunteerInfo | null>(null);
  const [step, setStep] = useState<FlowStep>("intro");
  const [selectedRating, setSelectedRating] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);

  const isMounted = useRef(true);
  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // Validate token on mount
  useEffect(() => {
    if (!token) return;

    fetch(`${API_URL}/api/verify/${token}`)
      .then(async (r) => {
        if (!isMounted.current) return;
        if (r.ok) {
          const data: VolunteerInfo = await r.json();
          setInfo(data);
          setTokenState("valid");
          return;
        }
        const body = await r.json().catch(() => ({}));
        const code = body?.detail?.code ?? "";
        if (code === "TOKEN_EXPIRED") setTokenState("expired");
        else if (code === "TOKEN_ALREADY_USED") setTokenState("used");
        else setTokenState("invalid");
      })
      .catch(() => {
        if (isMounted.current) setTokenState("invalid");
      });
  }, [token]);

  async function handleSubmit(comment: string | null) {
    if (!token || !selectedRating) return;
    setSubmitting(true);

    try {
      const r = await fetch(`${API_URL}/api/verify/${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating: selectedRating, comment }),
      });

      if (!isMounted.current) return;

      if (r.ok || r.status === 201) {
        setStep("success");
      } else {
        const body = await r.json().catch(() => ({}));
        const code = body?.detail?.code ?? "";
        if (code === "TOKEN_ALREADY_USED") setTokenState("used");
        else setTokenState("invalid");
      }
    } catch {
      if (isMounted.current) setTokenState("invalid");
    } finally {
      if (isMounted.current) setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-background">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center">
          <p className="text-lg font-black tracking-tight text-foreground">VOLAURA</p>
          <p className="text-xs text-muted-foreground">{t("verify.pageSubtitle")}</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-border bg-card p-6">
          {/* Loading */}
          {tokenState === "loading" && (
            <div className="flex flex-col items-center gap-3 py-8">
              <div
                className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent"
                aria-label={t("common.loading")}
                role="status"
                aria-busy="true"
              />
              <p className="text-sm text-muted-foreground">{t("verify.validatingToken")}</p>
            </div>
          )}

          {/* Error states */}
          {(tokenState === "invalid" || tokenState === "expired" || tokenState === "used") && (
            <ErrorScreen state={tokenState} t={t} />
          )}

          {/* Valid token flow */}
          {tokenState === "valid" && info && (
            <AnimatePresence mode="wait">
              {step === "intro" && (
                <IntroScreen
                  key="intro"
                  info={info}
                  locale={locale}
                  onStart={() => setStep("rating")}
                  t={t}
                />
              )}
              {step === "rating" && (
                <RatingScreen
                  key="rating"
                  info={info}
                  locale={locale}
                  onSelect={(r) => { setSelectedRating(r); setStep("comment"); }}
                  t={t}
                />
              )}
              {step === "comment" && (
                <CommentScreen
                  key="comment"
                  rating={selectedRating}
                  onSubmit={handleSubmit}
                  submitting={submitting}
                  t={t}
                />
              )}
              {step === "success" && (
                <SuccessScreen
                  key="success"
                  info={info}
                  rating={selectedRating}
                  locale={locale}
                  t={t}
                />
              )}
            </AnimatePresence>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          {t("verify.poweredBy")}{" "}
          <Link href={`/${locale}`} className="text-primary hover:underline">
            Volaura
          </Link>
        </p>
      </div>
    </div>
  );
}
