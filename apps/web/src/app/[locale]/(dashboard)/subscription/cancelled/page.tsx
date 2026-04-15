"use client";

import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { CircleCheck } from "lucide-react";

export default function SubscriptionCancelledPage() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();

  return (
    <main className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full rounded-2xl border border-border bg-card p-8 text-center space-y-5">
        <div className="flex justify-center">
          <CircleCheck className="h-16 w-16 text-muted-foreground" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-bold">
          {t("subscription.cancelled.title", { defaultValue: "No charge was made" })}
        </h1>
        <p className="text-muted-foreground">
          {t("subscription.cancelled.description", {
            defaultValue: "You can reactivate your subscription any time.",
          })}
        </p>
        <div className="flex flex-col items-center gap-3">
          <button
            onClick={() => router.push(`/${locale}/dashboard`)}
            className="w-full rounded-xl bg-primary px-4 py-3 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            {t("subscription.cancelled.ctaDashboard", { defaultValue: "Back to dashboard" })}
          </button>
          <button
            onClick={() => router.push(`/${locale}/settings`)}
            className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-4 transition-colors"
          >
            {t("subscription.cancelled.ctaSettings", { defaultValue: "Settings" })}
          </button>
        </div>
      </div>
    </main>
  );
}
