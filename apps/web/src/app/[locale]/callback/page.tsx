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

    const supabase = createClient();

    // WHY: createBrowserClient is a singleton with detectSessionInUrl: true.
    // When the singleton was first created (on the login page), it stored the
    // code_verifier in document.cookie. On this callback page, detectSessionInUrl
    // causes the singleton to auto-initiate exchangeCodeForSession internally the
    // moment it sees ?code= in the URL. Calling exchangeCodeForSession() manually
    // a second time would attempt to reuse a single-use code → 401 from Supabase.
    //
    // SOLUTION: Do NOT call exchangeCodeForSession manually. Instead, listen via
    // onAuthStateChange which fires once the auto-exchange completes successfully.
    // A 5-second timeout guards against silent failures.

    const timeoutId = setTimeout(() => {
      if (!isMounted.current) return;
      console.error("[callback] Timed out waiting for SIGNED_IN event");
      router.replace(`/${locale}/login?message=oauth-error`);
    }, 5000);

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event !== "SIGNED_IN" || !session) return;

        clearTimeout(timeoutId);
        if (!isMounted.current) return;

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
            // Non-blocking — analytics loss is acceptable, auth must not fail
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
      }
    );

    return () => {
      clearTimeout(timeoutId);
      subscription.unsubscribe();
    };
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
