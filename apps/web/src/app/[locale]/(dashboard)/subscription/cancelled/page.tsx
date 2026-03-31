"use client";

import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { XCircle } from "lucide-react";

export default function SubscriptionCancelledPage() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();

  return (
    <main className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full rounded-2xl border border-border bg-card p-8 text-center space-y-5">
        <div className="flex justify-center">
          <XCircle className="h-16 w-16 text-muted-foreground" />
        </div>
        <h1 className="text-2xl font-bold">{t("subscription.cancelled.title", "No Charge Made")}</h1>
        <p className="text-muted-foreground">
          {t("subscription.cancelled.description", "You cancelled the checkout. Your trial is still active — you can subscribe anytime from Settings.")}
        </p>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => router.push(`/${locale}/dashboard`)}
            className="w-full rounded-xl bg-primary px-4 py-3 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            {t("subscription.cancelled.ctaDashboard", "Back to Dashboard")}
          </button>
          <button
            onClick={() => router.push(`/${locale}/settings`)}
            className="w-full rounded-xl border border-border px-4 py-3 font-medium hover:bg-muted transition-colors"
          >
            {t("subscription.cancelled.ctaSettings", "Go to Settings")}
          </button>
        </div>
      </div>
    </main>
  );
}
