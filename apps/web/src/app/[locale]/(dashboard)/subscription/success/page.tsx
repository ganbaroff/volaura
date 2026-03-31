"use client";

import { useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { CheckCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export default function SubscriptionSuccessPage() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    // Invalidate subscription + profile cache so dashboard reflects new status immediately
    queryClient.invalidateQueries({ queryKey: ["subscription"] });
    queryClient.invalidateQueries({ queryKey: ["profile"] });
  }, [queryClient]);

  return (
    <main className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full rounded-2xl border border-border bg-card p-8 text-center space-y-5">
        <div className="flex justify-center">
          <CheckCircle className="h-16 w-16 text-green-500" />
        </div>
        <h1 className="text-2xl font-bold">{t("subscription.success.title", "Subscription Active!")}</h1>
        <p className="text-muted-foreground">
          {t("subscription.success.description", "Welcome to Volaura Pro. Your access is now active — keep building your AURA.")}
        </p>
        {sessionId && (
          <p className="text-xs text-muted-foreground/60 font-mono break-all">
            {t("subscription.success.reference", "Reference")}: {sessionId.slice(0, 20)}…
          </p>
        )}
        <button
          onClick={() => router.push(`/${locale}/dashboard`)}
          className="w-full rounded-xl bg-primary px-4 py-3 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {t("subscription.success.cta", "Go to Dashboard")}
        </button>
      </div>
    </main>
  );
}
