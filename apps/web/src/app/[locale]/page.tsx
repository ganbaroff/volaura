import initTranslations from "@/app/i18n";
import Link from "next/link";

interface PageProps {
  params: Promise<{ locale: string }>;
}

export default async function LandingPage({ params }: PageProps) {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="mb-4 text-5xl font-bold tracking-tight">
          {t("landing.title")}
        </h1>
        <p className="mb-8 text-lg text-muted-foreground">
          {t("landing.subtitle")}
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href={`/${locale}/login`}
            className="rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            {t("landing.getStarted")}
          </Link>
          <Link
            href={`/${locale}/b2b/search`}
            className="rounded-lg border border-border px-6 py-3 font-medium transition-colors hover:bg-accent"
          >
            {t("landing.forOrganizations")}
          </Link>
        </div>
      </div>
    </main>
  );
}
