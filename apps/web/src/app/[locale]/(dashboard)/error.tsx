"use client";

import { useTranslation } from "react-i18next";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h2 className="text-xl font-semibold text-on-surface">
        {t("error.generic")}
      </h2>
      <p className="max-w-md text-on-surface-variant">
        {t("error.tryAgain")}
      </p>
      <button
        onClick={reset}
        className="rounded-lg bg-primary px-4 py-2 text-on-primary transition-colors hover:bg-primary/90"
      >
        {t("error.retry")}
      </button>
    </div>
  );
}
