"use client";

import { useTranslation } from "react-i18next";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center px-4">
      <h2 className="text-xl font-semibold text-on-surface">
        {t("error.generic")}
      </h2>
      <p className="max-w-md text-on-surface-variant">
        {t("error.tryAgain")}
      </p>
      <div className="flex gap-3">
        <button
          onClick={reset}
          className="rounded-lg bg-primary px-4 py-2 text-on-primary transition-colors hover:bg-primary/90"
        >
          {t("error.retry")}
        </button>
        <Link
          href={`/${locale}/login`}
          className="rounded-lg border border-outline px-4 py-2 text-on-surface transition-colors hover:bg-surface-container"
        >
          {t("common.login", { defaultValue: "Log in" })}
        </Link>
      </div>
    </div>
  );
}
