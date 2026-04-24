"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/auth-store";
import { readAndClearAttribution, readAndClearFromStorage } from "@/components/utm-capture";
import { OAUTH_META_KEY } from "@/components/ui/social-auth-buttons";
import { API_BASE } from "@/lib/api/client";
import { getCallbackProfileRoute } from "./route-decision";

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
    // OAuth provider returned an explicit error before even reaching Supabase
    if (errorParam) {
      router.replace(`/${locale}/login?message=oauth-error`);
      return;
    }

    const code = searchParams.get("code");
    if (!code) {
      router.replace(`/${locale}/login?message=oauth-error`);
      return;
    }

    // WHY (INC-018, 2026-04-17): two entry paths reach this callback with opposite
    // exchange needs, and auto-exchange by `_initialize()` cannot be disabled from
    // userland. `@supabase/ssr` 0.6.0's `createBrowserClient` HARDCODES
    // `detectSessionInUrl: isBrowser()` AFTER spreading user options, so any
    // `auth: { detectSessionInUrl: false }` override is silently ignored.
    //
    //   Path A — external OAuth redirect (fresh page load from Google):
    //     New `createBrowserClient` singleton is built on /callback. Its first
    //     `_initialize()` sees `?code=` in the URL and auto-exchanges it. The
    //     PKCE `code_verifier` cookie is consumed. If we *also* call
    //     `exchangeCodeForSession(code)` explicitly, whichever runs second hits
    //     "PKCE code verifier not found in storage" and bounces user to /login.
    //
    //   Path B — SPA navigation (user clicked in-app link that carried ?code=):
    //     Singleton already exists (built on login page with no ?code=).
    //     `_initialize()` already ran and did NOT auto-exchange (URL had no code
    //     at construction time). We MUST call `exchangeCodeForSession(code)`
    //     ourselves or the session never lands. This is the INC-017 case.
    //
    // FIX: `getSession()` awaits the internal `_initializePromise` lock, so if
    // `_initialize()` auto-exchanged (Path A), we get a real session back. If
    // it didn't (Path B), we get null and fall through to the explicit exchange.
    // Single code path, covers both, no race, no double-consume of the verifier.

    void (async () => {
      const supabase = createClient();

      // Path A awaits init; returns real session when auto-exchange ran.
      // Path B returns null session; fall through to explicit exchange.
      const { data: initial } = await supabase.auth.getSession();
      let session = initial.session;

      if (!isMounted.current) return;

      if (!session) {
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);
        if (!isMounted.current) return;
        if (error || !data.session) {
          router.replace(`/${locale}/login?message=oauth-error`);
          return;
        }
        session = data.session;
      }

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

      // Route new users (no profile yet) to onboarding, returning users to dashboard.
      // Anything else is ambiguous runtime truth and must not silently pretend
      // the user has a valid profile/dashboard path.
      try {
        const res = await fetch(`${API_BASE}/profiles/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!isMounted.current) return;
        router.replace(getCallbackProfileRoute(locale, res.status));
        return;
      } catch {
        router.replace(getCallbackProfileRoute(locale, "network-error"));
        return;
      }
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
