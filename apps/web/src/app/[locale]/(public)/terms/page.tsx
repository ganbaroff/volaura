import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import initTranslations from "@/app/i18n";

export const metadata: Metadata = {
  title: "Terms of Service — Volaura",
};

export default async function TermsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b border-white/10 bg-surface-container/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link
            href={`/${locale}`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t("terms.back")}
          </Link>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold font-headline mb-2">{t("terms.title")}</h1>
          <p className="text-muted-foreground text-sm">{t("terms.effectiveDate")}</p>
        </div>

        <div className="prose prose-invert prose-sm max-w-none space-y-10 text-sm leading-relaxed">

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s1.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s1.body")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s2.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s2.body")}</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground mt-2">
              <li>{t("terms.s2.rule1")}</li>
              <li>{t("terms.s2.rule2")}</li>
              <li>{t("terms.s2.rule3")}</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s3.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s3.body")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s4.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s4.body")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s5.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s5.body")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s6.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s6.body")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("terms.s7.title")}</h2>
            <p className="text-muted-foreground">{t("terms.s7.body")}</p>
            <p className="text-muted-foreground mt-2">
              {t("terms.s7.contact")}{" "}
              <a href="mailto:hello@volaura.app" className="text-primary underline">
                hello@volaura.app
              </a>
            </p>
          </section>

        </div>

        <div className="mt-16 pt-8 border-t border-white/10 text-center text-xs text-muted-foreground">
          <p>
            © 2026 Volaura ·{" "}
            <Link href={`/${locale}/privacy`} className="hover:text-foreground transition-colors">
              {t("terms.privacyLink")}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
