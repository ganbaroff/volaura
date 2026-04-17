"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Building2, Search, CheckCircle2, Globe, ExternalLink } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useOrganizations } from "@/hooks/queries/use-organizations";
import type { OrganizationResponse } from "@/lib/api/types";
import { cn } from "@/lib/utils/cn";

// ── Stagger ────────────────────────────────────────────────────────────────────

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};
const card = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: "easeOut" as const } },
};

// ── Org card ───────────────────────────────────────────────────────────────────

function OrgCard({ org, onSelect }: { org: OrganizationResponse; onSelect: () => void }) {
  const { t } = useTranslation();

  const initial = org.name.trim()[0]?.toUpperCase() ?? "O";

  return (
    <motion.div
      variants={card}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(); } }}
      className="group relative flex flex-col gap-3 rounded-2xl border border-border bg-surface-container-low p-5 cursor-pointer hover:border-primary/40 hover:bg-surface-container transition-all"
    >
      {/* Avatar */}
      <div className="flex items-start gap-3">
        {org.logo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={org.logo_url} alt={org.name} className="size-10 rounded-xl object-cover shrink-0 border border-border" />
        ) : (
          <span className="size-10 rounded-xl bg-primary/15 flex items-center justify-center shrink-0 text-base font-bold text-primary">
            {initial}
          </span>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="text-sm font-semibold text-on-surface truncate group-hover:text-primary transition-colors">{org.name}</p>
            {org.verified_at && (
              <CheckCircle2 className="size-3.5 text-primary shrink-0" aria-label={t("orgs.verified")} />
            )}
          </div>
          {org.trust_score != null && (
            <p className="text-xs text-on-surface-variant">
              {t("orgs.trustScore")}: <span className="text-primary font-medium">{org.trust_score!.toFixed(1)}</span>
            </p>
          )}
        </div>

        <ExternalLink className="size-4 text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity shrink-0" aria-hidden="true" />
      </div>

      {org.description && (
        <p className="text-xs text-on-surface-variant line-clamp-2 leading-relaxed">{org.description}</p>
      )}

      {/* Footer */}
      {(org.website || org.contact_email) && (
        <div className="flex items-center gap-3 pt-1 border-t border-border/50">
          {org.website && (
            <a
              href={org.website}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <Globe className="size-3" aria-hidden="true" /> {t("orgs.website")}
            </a>
          )}
        </div>
      )}
    </motion.div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function OrganizationsDiscoveryPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();

  const [query, setQuery] = useState("");

  const { data: orgs, isLoading, error } = useOrganizations({ limit: 50 });

  const filtered = orgs?.filter((o) =>
    query.length === 0 ||
    o.name.toLowerCase().includes(query.toLowerCase()) ||
    (o.description ?? "").toLowerCase().includes(query.toLowerCase())
  ) ?? [];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <div className="relative overflow-hidden border-b border-border bg-surface-container-low px-6 py-12">
        {/* Ambient glow */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 size-[400px] rounded-full bg-primary/8 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-2xl text-center">
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: "easeOut" as const }}>
            <Building2 className="mx-auto mb-3 size-10 text-primary" aria-hidden="true" />
            <h1 className="font-headline text-3xl font-bold text-on-surface">{t("orgs.discoveryTitle")}</h1>
            <p className="mt-2 text-on-surface-variant">{t("orgs.discoverySubtitle")}</p>
          </motion.div>

          {/* Search */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1, ease: "easeOut" as const }}
            className="relative mt-6"
          >
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-4 text-on-surface-variant" aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("orgs.searchPlaceholder")}
              aria-label={t("orgs.searchPlaceholder")}
              className="w-full rounded-2xl border border-outline-variant bg-surface-container px-4 py-3 pl-10 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 transition-all"
            />
          </motion.div>
        </div>
      </div>

      {/* Grid */}
      <div className="mx-auto max-w-3xl px-4 py-8">
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2" role="status" aria-label="Loading">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-2xl border border-border bg-surface-container-low p-5 space-y-3">
                <div className="flex items-start gap-3">
                  <Skeleton className="size-10 rounded-xl" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-error/30 bg-error/10 p-4 text-center text-sm text-error">
            {t("error.generic")}
          </div>
        )}

        {!isLoading && !error && filtered.length === 0 && (
          <div className="py-16 text-center space-y-2">
            <Building2 className="mx-auto size-10 text-on-surface-variant" aria-hidden="true" />
            <p className="text-sm text-on-surface-variant">
              {query ? t("orgs.noSearchResults") : t("orgs.noOrgsYet")}
            </p>
          </div>
        )}

        {!isLoading && filtered.length > 0 && (
          <>
            <p className="mb-4 text-xs text-on-surface-variant">
              {t("orgs.showing", { count: filtered.length })}
            </p>
            <motion.div
              variants={stagger}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 gap-4 sm:grid-cols-2"
            >
              {filtered.map((org) => (
                <OrgCard
                  key={org.id}
                  org={org}
                  onSelect={() => router.push(`/${locale}/organizations/${org.id}`)}
                />
              ))}
            </motion.div>
          </>
        )}

        {/* CTA for orgs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.3, ease: "easeOut" as const }}
          className="mt-12 rounded-2xl border border-dashed border-primary/30 bg-primary/5 p-6 text-center"
        >
          <h3 className="font-semibold text-on-surface">{t("orgs.ctaTitle")}</h3>
          <p className="mt-1 text-sm text-on-surface-variant">{t("orgs.ctaSubtitle")}</p>
          <button
            onClick={() => router.push(`/${locale}/my-organization`)}
            className={cn(
              "mt-4 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-on-primary",
              "hover:opacity-90 transition-opacity"
            )}
          >
            {t("orgs.ctaButton")}
          </button>
        </motion.div>
      </div>
    </div>
  );
}
