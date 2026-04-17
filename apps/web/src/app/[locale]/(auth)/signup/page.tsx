"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import Link from "next/link";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/auth-store";
import { API_BASE } from "@/lib/api/client";
import type { SignupStatusResponse, ValidateInviteResponse } from "@/lib/api/generated/types.gen";
import { SocialAuthButtons } from "@/components/ui/social-auth-buttons";

type AccountType = "professional" | "organization";
type OrgType = "ngo" | "corporate" | "government" | "startup" | "academic" | "other";

export default function SignupPage() {
  return (
    <Suspense fallback={
      <div className="space-y-6" role="status" aria-live="polite">
        <div className="space-y-2 text-center">
          <Skeleton className="h-8 w-48 mx-auto" />
          <Skeleton className="h-4 w-64 mx-auto" />
        </div>
        <div className="flex justify-center gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-6 w-28 rounded-full" />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-10 w-full rounded-md" />
          <Skeleton className="h-10 w-full rounded-md" />
        </div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full rounded-md" />
            </div>
          ))}
        </div>
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
    }>
      <SignupForm />
    </Suspense>
  );
}

function SignupForm() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const setSession = useAuthStore((s) => s.setSession);
  const searchParams = useSearchParams();

  // Pre-select org type if coming from "Find talent" hero CTA
  const initialType: AccountType = searchParams.get("type") === "organization" ? "organization" : "professional";
  const [accountType, setAccountType] = useState<AccountType>(initialType);
  const [orgType, setOrgType] = useState<OrgType | "">("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Pre-fill from ?invite= URL param — warm invite link recipients skip manual entry
  const [inviteCode, setInviteCode] = useState(searchParams.get("invite") ?? "");
  const [privacyConsented, setPrivacyConsented] = useState(false);
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [celebrationNumber, setCelebrationNumber] = useState<number | null>(null);
  // If ?invite= param present, treat as invite-only immediately (avoids 200-400ms flicker)
  const [openSignup, setOpenSignup] = useState<boolean | null>(
    searchParams.get("invite") ? false : null
  );
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    // Check whether signup requires an invite code
    fetch(`${API_BASE}/auth/signup-status`)
      .then((r) => r.json() as Promise<SignupStatusResponse>)
      .then((data) => { if (isMounted.current) setOpenSignup(data.open_signup ?? true); })
      .catch(() => { if (isMounted.current) setOpenSignup(true); }); // fail open on network error
    return () => { isMounted.current = false; };
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!privacyConsented) {
      setError(t("auth.privacyConsentRequired", { defaultValue: "Please accept the privacy policy to continue." }));
      return;
    }
    if (!ageConfirmed) {
      setError(t("auth.ageConfirmRequired", { defaultValue: "Please confirm you are 16 or older to continue." }));
      return;
    }
    setError(null);
    setLoading(true);

    try {
      // Invite gate: validate code before creating Supabase account
      if (openSignup === false) {
        const validateRes = await fetch(`${API_BASE}/auth/validate-invite`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ invite_code: inviteCode }),
        });
        if (!validateRes.ok) {
          setError(t("auth.inviteCodeInvalid", { defaultValue: "Invalid invite code. Please try again." }));
          return;
        }
        const validateData = (await validateRes.json()) as ValidateInviteResponse;
        if (!validateData.valid) {
          setError(t("auth.inviteCodeInvalid", { defaultValue: "Invalid invite code. Please try again." }));
          return;
        }
      }

      const supabase = createClient();
      const { data, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            username: username.trim().toLowerCase(),
            account_type: accountType,
            org_type: accountType === "organization" ? orgType || null : null,
            // GDPR consent capture — stored in user metadata for audit trail.
            // terms_accepted_at is written to profiles table during onboarding.
            age_confirmed: true,
            terms_version: "1.0",
            terms_accepted_at: new Date().toISOString(),
          },
        },
      });

      if (authError) {
        // Shame-free (Law 3): no raw Supabase text to the user.
        // We still log the real error for debugging.
        console.error("[signup] supabase auth error:", authError);
        setError(
          t("auth.errorGeneric", {
            defaultValue: "Something's off on our side — please try again in a moment.",
          })
        );
        return;
      }

      if (!data.session) {
        router.push(`/${locale}/login?message=check-email`);
        return;
      }

      setSession(data.session);

      // Fetch profile to get registration_number for celebration message
      try {
        const profileRes = await fetch(`${API_BASE}/profiles/me`, {
          headers: { Authorization: `Bearer ${data.session.access_token}` },
        });
        if (profileRes.ok) {
          const profileData = await profileRes.json();
          const regNum: number | null = profileData?.registration_number ?? null;
          if (regNum != null && isMounted.current) {
            setCelebrationNumber(regNum);
            await new Promise((resolve) => setTimeout(resolve, 2200));
          }
        }
      } catch {
        // Non-blocking — proceed to onboarding even if profile fetch fails
      }

      if (isMounted.current) {
        router.push(`/${locale}/onboarding`);
      }
    } catch (err) {
      // Network failure, CORS, JSON parse — never silent.
      console.error("[signup] unexpected error:", err);
      setError(
        t("auth.errorGeneric", {
          defaultValue: "Something's off on our side — please try again in a moment.",
        })
      );
    } finally {
      setLoading(false);
    }
  }

  if (celebrationNumber != null) {
    return (
      <div className="space-y-6 text-center">
        <div className="text-4xl">🚀</div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-foreground">
            {t("auth.welcomeAboard", { defaultValue: "Welcome aboard!" })}
          </h2>
          <p className="text-lg font-mono font-semibold text-primary">
            #{String(celebrationNumber).padStart(4, "0")}
          </p>
          <p className="text-sm text-muted-foreground">
            {t("auth.foundingMemberMessage", {
              defaultValue: "You're a Founding Member. Your number is reserved forever.",
            })}
          </p>
        </div>
        <div className="flex justify-center">
          <Skeleton className="h-5 w-32" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold">{t("auth.signupTitle")}</h1>
        <p className="text-sm text-muted-foreground">{t("auth.signupSubtitle")}</p>
      </div>

      {/* Trust signal pills — reduces friction for GDPR-adjacent markets */}
      <div className="flex flex-wrap justify-center gap-2">
        {[
          t("auth.trustNoCv", { defaultValue: "No CV required" }),
          t("auth.trustDataPrivate", { defaultValue: "Data stays private" }),
          t("auth.trustNoSpam", { defaultValue: "No spam, ever" }),
        ].map((label) => (
          <span
            key={label}
            className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-3 py-1 text-xs text-muted-foreground"
          >
            <svg className="h-3 w-3 text-primary" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
            </svg>
            {label}
          </span>
        ))}
      </div>

      {/* Social auth — only available when invite gate is off */}
      {openSignup !== false && (
        <SocialAuthButtons
          redirectTo={`${typeof window !== "undefined" ? window.location.origin : ""}/${locale}/callback`}
          meta={{ account_type: accountType, ...(orgType ? { org_type: orgType } : {}) }}
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Role selection */}
        <div className="space-y-2">
          <p className="text-sm font-medium">{t("auth.accountTypeLabel")}</p>
          <div className="grid grid-cols-2 gap-3">
            {(["professional", "organization"] as AccountType[]).map((type) => (
              <button
                key={type}
                type="button"
                aria-pressed={accountType === type}
                onClick={() => setAccountType(type)}
                className={`rounded-lg border-2 p-3 text-left transition-colors ${
                  accountType === type
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="text-sm font-medium">
                  {t(`auth.accountType${type === "professional" ? "Professional" : "Org"}`)}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {t(`auth.accountType${type === "professional" ? "Professional" : "Org"}Desc`)}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Org type (only for organizations) */}
        {accountType === "organization" && (
          <div className="space-y-1.5">
            <label htmlFor="org-type" className="text-sm font-medium">{t("auth.orgTypeLabel")}</label>
            <select
              id="org-type"
              value={orgType}
              onChange={(e) => setOrgType(e.target.value as OrgType)}
              required
              className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">—</option>
              <option value="ngo">{t("auth.orgTypeNgo")}</option>
              <option value="corporate">{t("auth.orgTypeCorporate")}</option>
              <option value="government">{t("auth.orgTypeGov")}</option>
              <option value="startup">{t("auth.orgTypeStartup")}</option>
              <option value="academic">{t("auth.orgTypeAcademic")}</option>
              <option value="other">{t("auth.orgTypeOther")}</option>
            </select>
          </div>
        )}

        {/* Username */}
        <div className="space-y-1.5">
          <label htmlFor="username" className="text-sm font-medium">
            {t("auth.username")}
          </label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            required
            minLength={3}
            maxLength={30}
            pattern="[\-a-zA-Z0-9_\u0259\u011F\u0131\u00F6\u00FC\u015F\u00E7\u018F\u011E\u0130\u00D6\u00DC\u015E\u00C7]+"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          />
        </div>

        {/* Email */}
        <div className="space-y-1.5">
          <label htmlFor="email" className="text-sm font-medium">
            {t("auth.email")}
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          />
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <label htmlFor="password" className="text-sm font-medium">
            {t("auth.password")}
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              minLength={8}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="flex h-10 w-full rounded-md border border-border bg-background px-3 pr-10 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? t("auth.hidePassword", { defaultValue: "Hide password" }) : t("auth.showPassword", { defaultValue: "Show password" })}
            >
              {showPassword ? "👁" : "👁‍🗨"}
            </button>
          </div>
          {/* Password requirements — inline hint (Security agent: conversion killer without this) */}
          <p className="text-xs text-muted-foreground">
            {t("auth.passwordHint", { defaultValue: "8+ characters, uppercase, lowercase, and a number." })}
          </p>
        </div>

        {/* Invite code — only shown when signup is invite-only */}
        {openSignup === false && (
          <div className="space-y-1.5">
            <label htmlFor="invite-code" className="text-sm font-medium">
              {t("auth.inviteCodeLabel", { defaultValue: "Invite code" })}
            </label>
            <input
              id="invite-code"
              type="text"
              required
              autoComplete="off"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              placeholder={t("auth.inviteCodePlaceholder", { defaultValue: "Enter your invite code" })}
              className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            />
            <p className="text-xs text-muted-foreground">
              {t("auth.inviteCodeHint", { defaultValue: "Volaura is currently invite-only. Ask a friend or contact us to get a code." })}
            </p>
          </div>
        )}

        {/* Privacy consent — AZ-native framing */}
        <label className="flex items-start gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={privacyConsented}
            onChange={(e) => setPrivacyConsented(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-border accent-primary flex-shrink-0"
          />
          <span className="text-sm text-muted-foreground">
            {t("auth.privacyConsent")}
          </span>
        </label>

        {/* Age confirmation — GDPR Art. 8 (16+ threshold) */}
        <label className="flex items-start gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={ageConfirmed}
            onChange={(e) => setAgeConfirmed(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-border accent-primary flex-shrink-0"
          />
          <span className="text-sm text-muted-foreground">
            {t("auth.ageConfirm", { defaultValue: "I confirm I am 16 years of age or older." })}
          </span>
        </label>

        {error && (
          <p role="alert" className="rounded-md bg-error-container p-3 text-sm text-on-error-container">{error}</p>
        )}

        {(!privacyConsented || !ageConfirmed) && !loading && (
          <p className="text-xs text-muted-foreground text-center -mb-1">
            {t("auth.checkboxesRequired", { defaultValue: "Please tick both checkboxes above to continue" })}
          </p>
        )}
        <button
          type="submit"
          disabled={loading || !privacyConsented || !ageConfirmed || (openSignup === false && !inviteCode.trim())}
          className="h-10 w-full rounded-md bg-primary font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 inline size-4 animate-spin" aria-hidden="true" />
              {t("auth.creatingAccount")}
            </>
          ) : (
            t("auth.signupAction")
          )}
        </button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        {t("auth.hasAccount")}{" "}
        <Link
          href={`/${locale}/login`}
          className="font-medium text-foreground underline underline-offset-4"
        >
          {t("auth.login")}
        </Link>
      </p>
    </div>
  );
}
