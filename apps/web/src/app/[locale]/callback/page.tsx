"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/auth-store";
import { readAndClearAttribution, readAndClearFromStorage } from "@/components/utm-capture";
import { OAUTH_META_KEY } from "@/components/ui/social-auth-buttons";
import { API_BASE } from "@/lib/api/client";

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">Loading…</p>
          </div>
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}

function AuthCallbackContent() {
  const { locale } = useParams<{ locale: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { t } = useTranslation();
  const setSession = useAuthStore((s) => s.setSession);
  const isMounted = useRef(true);
  const didRun = useRef(false);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    // Guard: only run once (React StrictMode double-invoke protection)
    if (didRun.current) return;
    didRun.current = true;

    const errorParam = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");

    // OAuth provider returned an explicit error before even reaching Supabase
    if (errorParam) {
      console.error("[callback] OAuth error:", errorParam, errorDescription);
      router.replace(`/${locale}/login?message=oauth-error`);
      return;
    }

    const code = searchParams.get("code");
    if (!code) {
      console.error("[callback] Missing ?code= in callback URL");
      router.replace(`/${locale}/login?message=oauth-error`);
      return;
    }

    // WHY (INC-017, 2026-04-15): previous implementation relied on the singleton
    // `createBrowserClient` auto-calling exchangeCodeForSession when it "sees"
    // ?code= via detectSessionInUrl. That assumption is false when the singleton
    // was first constructed on the login page (no ?code= in URL) — _initialize()
    // runs once at construction, does NOT re-check the URL on subsequent pages,
    // so the auto-exchange never fires. Result: session never persists, user
    // bounces back to login. Repeat bug reported by CEO 2026-04-15.
    //
    // FIX: explicitly call exchangeCodeForSession(code). The code_verifier is
    // still in document.cookie from signInWithOAuth, so the exchange works.
    // No double-exchange risk because auto-exchange never runs for a reused
    // singleton (the original concern in commit 1e26ccc was misdiagnosed).

    void (async () => {
      const supabase = createClient();
      const { data, error } = await supabase.auth.exchangeCodeForSession(code);

      if (!isMounted.current) return;

      if (error || !data.session) {
        console.error("[callback] exchangeCodeForSession failed:", error?.message);
        router.replace(`/${locale}/login?message=oauth-error`);
        return;
      }

      const session = data.session;
      setSession(session);

      // Attribution + OAuth metadata capture (fire-and-forget, non-blocking)
      const attribution = readAndClearAttribution();
      const oauthMeta = readAndClearFromStorage(OAUTH_META_KEY);
      const payload = { ...attribution, ...oauthMeta };
      if (Object.keys(payload).length > 0) {
        fetch(`${API_BASE}/profiles/me`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify(payload),
        }).catch(() => {
          // Non-blocking — analytics loss acceptable, auth must not fail
        });
      }

      // Honour ?next= redirect (relative paths only, prevents open redirect)
      const rawNext = searchParams.get("next");
      if (rawNext?.startsWith("/") && !rawNext.startsWith("//")) {
        router.replace(rawNext);
        return;
      }

      // Route new users (no profile yet) to onboarding, returning users to dashboard
      try {
        const res = await fetch(`${API_BASE}/profiles/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!isMounted.current) return;
        if (res.status === 404) {
          router.replace(`/${locale}/onboarding`);
          return;
        }
      } catch {
        // Network error — fall through to dashboard
      }

      router.replace(`/${locale}/dashboard`);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground">{t("auth.signingIn")}</p>
      </div>
    </div>
  );
}
