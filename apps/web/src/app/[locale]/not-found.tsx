"use client";

import { useTranslation } from "react-i18next";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useParams<{ locale: string }>();
  const locale = params?.locale ?? "en";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-4 text-center">
      <p className="text-6xl font-bold tabular-nums text-primary/30">404</p>
      <div className="space-y-2">
        <h1 className="text-xl font-semibold text-on-surface">
          {t("error.notFound", { defaultValue: "Page not found" })}
        </h1>
        <p className="text-sm text-on-surface-variant">
          {t("error.notFoundDesc", { defaultValue: "The page you're looking for doesn't exist or was moved." })}
        </p>
      </div>
      <Button onClick={() => router.push(`/${locale}/dashboard`)}>
        {t("nav.dashboard", { defaultValue: "Go to Dashboard" })}
      </Button>
    </div>
  );
}
