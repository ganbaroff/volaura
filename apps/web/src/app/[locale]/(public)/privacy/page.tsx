import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import initTranslations from "@/app/i18n";

export const metadata: Metadata = {
  title: "Privacy Policy — Volaura",
};

export default async function PrivacyPage({
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
            {t("privacy.back")}
          </Link>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold font-headline mb-2">{t("privacy.title")}</h1>
          <p className="text-muted-foreground text-sm">{t("privacy.effectiveDate")}</p>
        </div>

        <div className="prose prose-invert prose-sm max-w-none space-y-10 text-sm leading-relaxed">

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s1.title")}</h2>
            <p className="text-muted-foreground">{t("privacy.s1.body")}</p>
            <p className="text-muted-foreground mt-2">
              {t("privacy.s1.contact")}{" "}
              <a href="mailto:hello@volaura.app" className="text-primary underline">
                hello@volaura.app
              </a>
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s2.title")}</h2>
            <p className="text-muted-foreground">{t("privacy.s2.collected")}</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground mt-2">
              <li>{t("privacy.s2.item1")}</li>
              <li>{t("privacy.s2.item2")}</li>
              <li>{t("privacy.s2.item3")}</li>
              <li>{t("privacy.s2.item4")}</li>
            </ul>
            <p className="text-muted-foreground mt-3">{t("privacy.s2.notCollected")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s3.title")}</h2>
            <p className="text-muted-foreground">{t("privacy.s3.body")}</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground mt-2">
              <li>{t("privacy.s3.reason1")}</li>
              <li>{t("privacy.s3.reason2")}</li>
              <li>{t("privacy.s3.reason3")}</li>
            </ul>
            <p className="text-muted-foreground mt-2">{t("privacy.s3.noSell")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s4.title")}</h2>
            <p className="text-muted-foreground">{t("privacy.s4.body")}</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground mt-2">
              <li>{t("privacy.s4.item1")}</li>
              <li>{t("privacy.s4.item2")}</li>
              <li>{t("privacy.s4.item3")}</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s5.title")}</h2>
            <p className="text-muted-foreground mb-2">{t("privacy.s5.intro")}</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>{t("privacy.s5.access")}</li>
              <li>{t("privacy.s5.rectify")}</li>
              <li>{t("privacy.s5.delete")}</li>
              <li>{t("privacy.s5.portability")}</li>
              <li>{t("privacy.s5.object")}</li>
            </ul>
            <p className="text-muted-foreground mt-3">
              {t("privacy.s5.contact")}{" "}
              <a href="mailto:hello@volaura.app" className="text-primary underline">
                hello@volaura.app
              </a>
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s6.title")}</h2>
            <p className="text-muted-foreground">{t("privacy.s6.body")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold font-headline mb-3">{t("privacy.s7.title")}</h2>
            <p className="text-muted-foreground">{t("privacy.s7.body")}</p>
          </section>

        </div>

        <div className="mt-16 pt-8 border-t border-white/10 text-center text-xs text-muted-foreground">
          <p>
            © 2026 Volaura ·{" "}
            <Link href={`/${locale}/terms`} className="hover:text-foreground transition-colors">
              {t("privacy.termsLink")}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
