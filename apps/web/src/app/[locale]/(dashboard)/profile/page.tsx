"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { RefreshCw } from "lucide-react";
import { TopBar } from "@/components/layout/top-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { ProfileHeader } from "@/components/profile-view/profile-header";
import { ImpactMetrics } from "@/components/profile-view/impact-metrics";
import { SkillChips } from "@/components/profile-view/skill-chips";
import { ExpertVerifications } from "@/components/profile-view/expert-verifications";
import { ActivityTimeline } from "@/components/profile-view/activity-timeline";
import { useProfile, useMyVerifications } from "@/hooks/queries/use-profile";
import { useAuraScore } from "@/hooks/queries/use-aura";
import { useDashboardStats } from "@/hooks/queries/use-dashboard";
import { useMyEvents } from "@/hooks/queries/use-events";
import { ApiError } from "@/lib/api/client";
import type { TimelineEvent } from "@/components/profile-view/activity-timeline";

/* ─── Section wrapper ─── */
const sectionVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.32, ease: "easeOut" as const } },
};

function Section({
  title,
  children,
  delay = 0,
}: {
  title: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={sectionVariants}
      transition={{ delay }}
      className="space-y-3"
    >
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-0.5">
        {title}
      </p>
      <div className="rounded-xl border border-border bg-card p-4">{children}</div>
    </motion.div>
  );
}

/* ─── Skeleton loaders ─── */
function ProfileSkeleton() {
  return (
    <div className="space-y-5 p-4">
      <div className="flex items-start gap-4">
        <Skeleton className="size-16 rounded-full shrink-0" />
        <div className="flex-1 space-y-2 pt-1">
          <Skeleton className="h-4 w-2/5" />
          <Skeleton className="h-3 w-1/4" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-32 rounded-xl" />
      <Skeleton className="h-32 rounded-xl" />
    </div>
  );
}

/* ─── Referral Section ─── */
function ReferralSection({ username }: { username: string }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const link = typeof window !== "undefined"
    ? `${window.location.origin}/invite?ref=${username}`
    : `volaura.app/invite?ref=${username}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
    } catch {
      const el = document.createElement("textarea");
      el.value = link;
      el.style.position = "fixed";
      el.style.opacity = "0";
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        {t("profile.referralDesc", { defaultValue: "Share this link. When someone signs up and completes their first assessment, you both earn crystals." })}
      </p>
      <div className="flex items-center gap-2">
        <input
          readOnly
          value={link}
          className="flex-1 rounded-lg border border-input bg-surface-dim px-3 py-2 text-xs text-foreground"
          onClick={(e) => (e.target as HTMLInputElement).select()}
        />
        <button
          onClick={copy}
          className="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 min-w-[60px]"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </div>
  );
}

/* ─── Page ─── */
export default function ProfilePage() {
  const { locale } = useParams<{ locale: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const {
    data: profile,
    isLoading: profileLoading,
    error: profileError,
    refetch: refetchProfile,
  } = useProfile();

  const {
    data: aura,
    isLoading: auraLoading,
  } = useAuraScore();

  const { data: dashboardStats } = useDashboardStats();
  const { data: verifications } = useMyVerifications();
  const { data: myEvents } = useMyEvents();

  // Transform events into timeline format
  const timelineEvents: TimelineEvent[] = (myEvents || []).map((ev: Record<string, unknown>) => ({
    id: String(ev.id ?? ""),
    event_name: String(ev.title ?? "Event"),
    event_date: String(ev.date ?? ev.created_at ?? ""),
    role: ev.role ? String(ev.role) : null,
    participated: ev.status === "attended",
  }));

  const loading = profileLoading || auraLoading;

  // Handle 401
  useEffect(() => {
    if (profileError instanceof ApiError && profileError.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [profileError, locale, router]);

  if (loading) {
    return (
      <>
        <TopBar title={t("profile.title")} />
        <ProfileSkeleton />
      </>
    );
  }

  if (profileError || !profile) {
    return (
      <>
        <TopBar title={t("profile.title")} />
        <div className="flex flex-col items-center justify-center h-64 gap-3 text-center p-6">
          <p className="text-sm text-muted-foreground">{t("error.generic")}</p>
          <button
            onClick={() => refetchProfile()}
            className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
          >
            <RefreshCw className="size-3.5" aria-hidden="true" />
            {t("error.retry")}
          </button>
        </div>
      </>
    );
  }

  // Build competency scores array from AURA data
  const competencies = aura?.competency_scores
    ? Object.entries(aura.competency_scores).map(([competency_id, score]) => ({
        competency_id,
        score,
      }))
    : [];

  return (
    <>
      <TopBar title={t("profile.title")} />

      <div className="p-4 space-y-5 pb-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
        >
          <ProfileHeader
            profile={{
              username: profile.username,
              display_name: profile.display_name ?? null,
              bio: profile.bio ?? null,
              location: profile.location ?? null,
              languages: profile.languages ?? [],
              is_public: profile.is_public ?? false,
              avatar_url: profile.avatar_url ?? null,
              badge_tier: aura?.badge_tier ?? "none",
              total_score: aura?.total_score ?? null,
              registration_number: profile.registration_number,
              registration_tier: profile.registration_tier,
            }}
            locale={locale}
            isOwnProfile={true}
          />
        </motion.div>

        {/* Impact Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.1 }}
        >
          <ImpactMetrics
            data={{
              events_count: dashboardStats?.events_attended ?? 0,
              hours_volunteered: dashboardStats?.total_hours ?? 0,
              verified_skills: competencies.length,
            }}
          />
        </motion.div>

        {/* Verified Skills */}
        <Section title={t("profile.skills")} delay={0.2}>
          <SkillChips competencies={competencies} />
        </Section>

        {/* Referral Link */}
        {profile?.username && (
          <Section title={t("profile.referral", { defaultValue: "Invite Friends" })} delay={0.25}>
            <ReferralSection username={profile.username} />
          </Section>
        )}

        {/* Expert Verifications */}
        <Section title={t("profile.expertVerifications")} delay={0.3}>
          <ExpertVerifications verifications={verifications ?? []} />
        </Section>

        {/* Activity Timeline */}
        <Section title={t("profile.timeline")} delay={0.4}>
          <ActivityTimeline events={timelineEvents} />
        </Section>
      </div>
    </>
  );
}
