import type { Metadata } from "next";
import initTranslations from "@/app/i18n";
import { EventsList } from "@/components/events/events-list";
import { LandingNav } from "@/components/landing/landing-nav";
import { LandingFooter } from "@/components/landing/landing-footer";
import { getMockEvents } from "@/lib/mock-data";

interface EventsPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({
  params,
}: EventsPageProps): Promise<Metadata> {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);
  return {
    title: `Volaura — ${t("events.title")}`,
    description: t("events.noEventsSubtitle"),
  };
}

export default async function EventsPage({ params }: EventsPageProps) {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);

  // Session 11: replace with real API call — GET /api/events
  const events = getMockEvents();

  return (
    <>
      <LandingNav locale={locale} />
      <main className="mx-auto min-h-screen max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("events.title")}
          </h1>
          <p className="mt-2 text-muted-foreground">
            {t("events.noEventsSubtitle")}
          </p>
        </div>

        <EventsList events={events} locale={locale} />
      </main>
      <LandingFooter locale={locale} />
    </>
  );
}
