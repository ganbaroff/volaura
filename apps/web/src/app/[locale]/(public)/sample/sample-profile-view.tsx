"use client";

import { useTranslation } from "react-i18next";
import { useReducedMotion } from "framer-motion";
import { AuraRadarChart } from "@/components/aura/radar-chart";
import { BadgeDisplay } from "@/components/aura/badge-display";
import { getSampleProfile, type SampleVerifiedEvent, type CompetencyId } from "@/data/sample-profile";
import { MapPin, Calendar, Clock, CheckCircle2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useParams } from "next/navigation";

const COMPETENCY_LABELS: Record<string, string> = {
  communication: "Communication",
  reliability: "Reliability",
  english_proficiency: "English Proficiency",
  leadership: "Leadership",
  event_performance: "Event Performance",
  tech_literacy: "Tech Literacy",
  adaptability: "Adaptability",
  empathy_safeguarding: "Empathy & Safeguarding",
};

export function SampleProfileView() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const profile = getSampleProfile();
  const reducedMotion = useReducedMotion();
  void reducedMotion;

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-lg px-4 py-8">
        <Link href={`/${locale}`}>
          <Button variant="ghost" size="sm" className="mb-6 gap-2">
            <ArrowLeft className="h-4 w-4" />
            {t("common.back", { defaultValue: "Back" })}
          </Button>
        </Link>

        <div className="mb-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            {t("sample.label", { defaultValue: "Sample Profile" })}
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <div className="mb-6 text-center">
            <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <span className="text-2xl font-bold text-primary">
                {Math.round(profile.totalAuraScore)}
              </span>
            </div>
            <h1 className="text-lg font-semibold font-headline">
              {profile.displayName}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {locale === "az" ? profile.taglineAz : profile.tagline}
            </p>
            <div className="mt-3">
              <BadgeDisplay
                tier={profile.badgeTier}
                label={t(`badge.${profile.badgeTier}`, { defaultValue: profile.badgeTier })}
              />
            </div>
          </div>

          <AuraRadarChart
            competencyScores={profile.competencyScores}
            badgeTier={profile.badgeTier}
            size="md"
          />

          <div className="mt-6 space-y-2">
            {(Object.keys(profile.competencyScores) as CompetencyId[]).map((id) => (
              <div key={id} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {t(`competency.${id}`, { defaultValue: COMPETENCY_LABELS[id] ?? id })}
                </span>
                <span className="font-medium tabular-nums">{profile.competencyScores[id]}/100</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-widest">
            {t("sample.verifiedEvents", { defaultValue: "Verified Events" })}
          </h2>
          <div className="space-y-3">
            {profile.verifiedEvents.map((evt: SampleVerifiedEvent) => (
              <div
                key={evt.id}
                className="rounded-xl border border-border bg-card p-4"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium">
                      {locale === "az" ? evt.titleAz : evt.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {evt.organizerName}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {locale === "az" ? evt.locationAz : evt.location}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(evt.date).toLocaleDateString(
                          locale === "az" ? "az-AZ" : "en-GB"
                        )}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {evt.hoursContributed}h
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 text-center">
          <Link href={`/${locale}/auth/signup`}>
            <Button size="lg" className="w-full">
              {t("sample.cta", { defaultValue: "Build Your Own AURA Profile" })}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
