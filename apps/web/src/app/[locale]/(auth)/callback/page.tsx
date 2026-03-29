"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/auth-store";
import { readAndClearAttribution } from "@/components/utm-capture";
import { API_BASE } from "@/lib/api/client";

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-muted-foreground">Loading...</p></div>}>
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

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  useEffect(() => {
    const supabase = createClient();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (!isMounted.current) return;
      setSession(session);

      // Attribution capture: write UTM/referral data from localStorage to profile (fire-and-forget)
      if (session?.access_token) {
        const attribution = readAndClearAttribution();
        if (Object.keys(attribution).length > 0) {
          fetch(`${API_BASE}/api/profiles/me`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${session.access_token}`,
            },
            body: JSON.stringify(attribution),
          }).catch(() => {
            // Non-blocking — analytics loss is acceptable, auth must not fail
          });
        }
      }

      const rawNext = searchParams.get("next");
      // Only allow relative paths starting with "/" but not "//" (prevents protocol-relative open redirect)
      if (rawNext?.startsWith("/") && !rawNext.startsWith("//")) {
        router.replace(rawNext);
        return;
      }

      // Route new users (no profile) to onboarding, returning users to dashboard
      if (session?.access_token) {
        try {
          const res = await fetch(`${API_BASE}/api/profiles/me`, {
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
      }

      router.replace(`/${locale}/dashboard`);
    });

    return () => subscription.unsubscribe();
  }, [locale, router, searchParams, setSession]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">{t("auth.signingIn")}</p>
    </div>
  );
}
