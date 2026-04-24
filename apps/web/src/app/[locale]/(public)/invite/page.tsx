"use client";

/**
 * Beta invite landing page.
 *
 * Usage: /az/invite?code=BETA_01&utm_source=linkedin&utm_campaign=beta_week1
 *
 * - Validates invite code server-side (POST /api/invite/validate) — no allowlist in bundle
 * - Stores UTM params via utm-capture (already handled by auth callback)
 * - Redirects to /signup?type=professional (or ?type=organization) with code preserved
 * - Tracks invite code in localStorage so callback can log attribution
 *
 * Growth agent recommendation: skip waitlist entirely for warm contacts.
 * Warm contacts expect instant access — a waitlist queue kills conversion.
 */

import { Suspense, useEffect, useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle, XCircle } from "lucide-react";
import { API_BASE } from "@/lib/api/client";

export default function InvitePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><div className="w-full max-w-md space-y-4"><div className="h-10 w-56 mx-auto animate-pulse rounded bg-muted" /><div className="h-5 w-72 mx-auto animate-pulse rounded bg-muted" /><div className="h-12 w-full animate-pulse rounded-md bg-muted" /></div></div>}>
      <InviteContent />
    </Suspense>
  );
}

type ValidationState = "pending" | "valid" | "invalid";

function InviteContent() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useTranslation();

  const code = (searchParams.get("code") ?? "OPEN").toUpperCase();
  const type = searchParams.get("type") ?? "professional"; // "professional" | "organization"
  const isOrgCode = code.startsWith("ORG_");
  const accountType = isOrgCode ? "organization" : (type as string);

  const [validation, setValidation] = useState<ValidationState>("pending");
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    let cancelled = false;

    async function validate() {
      try {
        const res = await fetch(
          `${API_BASE}/invite/validate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code }),
          }
        );

        if (!res.ok) {
          if (!cancelled) setValidation("invalid");
          return;
        }

        const json = await res.json();
        const isValid: boolean = json?.data?.valid === true;

        if (cancelled) return;
        setValidation(isValid ? "valid" : "invalid");

        if (isValid) {
          // BUG-GROWTH-1 FIX: localStorage persists across page refreshes;
          // sessionStorage is lost on browser refresh — invite codes were silently
          // dropped before signup completed.
          localStorage.setItem("invite_code", code);
        }
      } catch {
        if (!cancelled) setValidation("invalid");
      }
    }

    void validate();
    return () => {
      cancelled = true;
    };
  }, [code]);

  // Auto-redirect countdown only starts after server confirms code is valid
  useEffect(() => {
    if (validation !== "valid") return;

    const interval = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearInterval(interval);
          router.push(`/${locale}/signup?type=${accountType}&invite=${code}`);
          return 0;
        }
        return c - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [validation, code, accountType, locale, router]);

  // Loading skeleton — matches final content shape (no spinner per design rules)
  if (validation === "pending") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-md text-center space-y-6">
          <div className="space-y-1">
            <h1 className="text-2xl font-black tracking-tight text-foreground">VOLAURA</h1>
            <div className="h-4 w-48 mx-auto animate-pulse rounded bg-muted" />
          </div>
          <div className="h-16 w-16 mx-auto animate-pulse rounded-full bg-muted" />
          <div className="space-y-2">
            <div className="h-6 w-40 mx-auto animate-pulse rounded bg-muted" />
            <div className="h-4 w-64 mx-auto animate-pulse rounded bg-muted" />
          </div>
          <div className="h-12 w-full animate-pulse rounded-xl bg-muted" />
        </div>
      </div>
    );
  }

  const isValid = validation === "valid";

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md text-center space-y-6"
      >
        {/* Logo */}
        <div className="space-y-1">
          <h1 className="text-2xl font-black tracking-tight text-foreground">VOLAURA</h1>
          <p className="text-sm text-muted-foreground">
            {t("landing.tagline", { defaultValue: "Prove your skills. Earn your AURA." })}
          </p>
        </div>

        {isValid ? (
          <>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className="flex justify-center"
            >
              <CheckCircle className="h-16 w-16 text-green-500" />
            </motion.div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-foreground">
                {t("invite.welcome", { defaultValue: "You're invited." })}
              </h2>
              <p className="text-muted-foreground">
                {isOrgCode
                  ? t("invite.orgSubtitle", { defaultValue: "Set up your organization profile and start finding verified talent." })
                  : t("invite.subtitle", { defaultValue: "Complete your first assessment. Get your AURA score. Get found." })
                }
              </p>
            </div>

            <Link
              href={`/${locale}/signup?type=${accountType}&invite=${code}`}
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground shadow-md transition-all hover:bg-primary/90"
            >
              {t("invite.cta", { defaultValue: "Create your account" })}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>

            <p className="text-xs text-muted-foreground">
              {t("invite.autoRedirect", {
                defaultValue: "Redirecting in {{count}}s...",
                count: countdown,
              })}
            </p>
          </>
        ) : (
          <>
            <div className="flex justify-center">
              <XCircle className="h-16 w-16 text-[#D4B4FF]" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-foreground">
                {t("invite.invalidTitle", { defaultValue: "This invite link is not valid." })}
              </h2>
              <p className="text-muted-foreground">
                {t("invite.invalidBody", { defaultValue: "Volaura is currently invite-only. Write to us in Telegram to request access." })}
              </p>
            </div>

            {/* Primary CTA: Telegram (AZ primary channel — 80% of target audience) */}
            <a
              href="https://t.me/yusifganbarov"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-[#2AABEE] px-7 py-3.5 text-base font-semibold text-white shadow-md transition-all hover:bg-[#229ED9]"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5 fill-current" aria-hidden="true">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.833.94z" />
              </svg>
              {t("invite.telegramCta", { defaultValue: "Request access on Telegram" })}
            </a>

            {/* Secondary CTA: LinkedIn */}
            <a
              href="https://linkedin.com/in/yusifganbarov"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl border border-border bg-background px-7 py-3 text-sm font-medium text-muted-foreground transition-all hover:bg-accent"
            >
              {t("invite.linkedinCta", { defaultValue: "Follow on LinkedIn for updates" })}
            </a>

            {/* Tertiary: manual code entry */}
            <p className="text-xs text-muted-foreground">
              {t("invite.hasCode", { defaultValue: "Already have a code?" })}{" "}
              <Link
                href={`/${locale}/signup`}
                className="underline underline-offset-4 hover:text-foreground"
              >
                {t("invite.enterManually", { defaultValue: "Enter it manually" })}
              </Link>
            </p>
          </>
        )}
      </motion.div>
    </div>
  );
}
