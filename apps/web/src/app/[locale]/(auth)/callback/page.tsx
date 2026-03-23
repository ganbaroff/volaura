"use client";

import { useEffect, useRef } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/auth-store";

export default function AuthCallbackPage() {
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

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!isMounted.current) return;
      setSession(session);
      const rawNext = searchParams.get("next");
      // Only allow relative paths starting with "/" but not "//" (prevents protocol-relative open redirect)
      const next = rawNext?.startsWith("/") && !rawNext.startsWith("//") ? rawNext : `/${locale}/dashboard`;
      router.replace(next);
    });

    return () => subscription.unsubscribe();
  }, [locale, router, searchParams, setSession]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">{t("auth.signingIn")}</p>
    </div>
  );
}
