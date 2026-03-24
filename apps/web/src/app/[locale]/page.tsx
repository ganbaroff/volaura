import type { Metadata } from "next";
import initTranslations from "@/app/i18n";

export const dynamic = "force-dynamic";
import { HeroSection } from "@/components/landing/hero-section";
import { ImpactTicker } from "@/components/landing/impact-ticker";
import { FeaturesGrid } from "@/components/landing/features-grid";
import { HowItWorks } from "@/components/landing/how-it-works";
import { OrgCta } from "@/components/landing/org-cta";
import { LandingNav } from "@/components/landing/landing-nav";
import { LandingFooter } from "@/components/landing/landing-footer";
import { getMockImpactStats } from "@/lib/mock-data";

interface LandingPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({
  params,
}: LandingPageProps): Promise<Metadata> {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);

  return {
    title: "Volaura — " + t("landing.heroTitle"),
    description: t("landing.heroSubtitle"),
    openGraph: {
      title: "Volaura — " + t("landing.heroTitle"),
      description: t("landing.heroSubtitle"),
      type: "website",
      locale: locale === "az" ? "az_AZ" : "en_US",
    },
  };
}

export default async function LandingPage({ params }: LandingPageProps) {
  const { locale } = await params;

  // Session 11: replace with real API call — GET /api/stats/public
  const stats = getMockImpactStats();

  return (
    <>
      {/* Skip to main content — must be FIRST focusable element in DOM */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <LandingNav locale={locale} />
      <main id="main-content">
        <HeroSection locale={locale} />
        <ImpactTicker stats={stats} />
        <FeaturesGrid />
        <HowItWorks />
        <OrgCta locale={locale} />
      </main>
      <LandingFooter locale={locale} />
    </>
  );
}
