"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { createClient } from "@/lib/supabase/client";

export default function ForgotPasswordPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-muted-foreground">Loading...</p></div>}>
      <ForgotPasswordContent />
    </Suspense>
  );
}

function ForgotPasswordContent() {
  const { locale } = useParams<{ locale: string }>();
  const { t } = useTranslation();

  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const supabase = createClient();
      const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/${locale}/reset-password`,
      });

      if (authError) {
        setError(authError.message);
        return;
      }

      setSent(true);
    } catch {
      setError(t("auth.unexpectedError"));
    } finally {
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <div className="space-y-6 text-center">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">{t("auth.checkEmailTitle")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("auth.checkEmailDesc", { email })}
          </p>
        </div>
        <p className="text-sm text-muted-foreground">
          {t("auth.noEmailReceived")}{" "}
          <button
            onClick={() => setSent(false)}
            className="font-medium text-foreground underline underline-offset-4"
          >
            {t("auth.tryAgain")}
          </button>
        </p>
        <Link
          href={`/${locale}/login`}
          className="block text-center text-sm font-medium text-foreground underline underline-offset-4"
        >
          {t("auth.backToLogin")}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold">{t("auth.forgotPasswordTitle")}</h1>
        <p className="text-sm text-muted-foreground">{t("auth.forgotPasswordSubtitle")}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="email" className="text-sm font-medium">
            {t("auth.email")}
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="h-10 w-full rounded-md bg-primary font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? t("auth.sendingReset") : t("auth.sendResetLink")}
        </button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        <Link
          href={`/${locale}/login`}
          className="font-medium text-foreground underline underline-offset-4"
        >
          {t("auth.backToLogin")}
        </Link>
      </p>
    </div>
  );
}
