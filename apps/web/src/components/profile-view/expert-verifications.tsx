"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { BadgeCheck, Building2 } from "lucide-react";

export interface ExpertVerification {
  id: string;
  verifier_name: string;       // e.g. "Anar Mammadov"
  verifier_org: string | null; // e.g. "COP29 Secretariat"
  competency_id: string;
  rating: number;              // 1-5
  comment: string | null;
  verified_at: string;         // ISO date
}

interface ExpertVerificationsProps {
  verifications: ExpertVerification[];
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
};
const row = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

function RatingDots({ rating }: { rating: number }) {
  return (
    <span className="flex gap-0.5" aria-label={`Rating: ${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          className={`size-1.5 rounded-full ${n <= rating ? "bg-primary" : "bg-muted"}`}
        />
      ))}
    </span>
  );
}

function Initials({ name }: { name: string }) {
  const parts = name.trim().split(" ");
  const letters =
    parts.length >= 2
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`
      : name.slice(0, 2);
  return <>{letters.toUpperCase()}</>;
}

export function ExpertVerifications({ verifications }: ExpertVerificationsProps) {
  const { t } = useTranslation();

  if (verifications.length === 0) {
    return (
      <div className="py-6 text-center space-y-2">
        <BadgeCheck className="size-8 text-muted-foreground mx-auto" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">{t("profile.noVerificationsYet")}</p>
      </div>
    );
  }

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className="space-y-3"
    >
      {verifications.map((v) => {
        const competencyLabel = t(`competency.${v.competency_id}`, {
          defaultValue: v.competency_id,
        });
        const date = new Date(v.verified_at).toLocaleDateString(undefined, {
          month: "short",
          year: "numeric",
        });

        return (
          <motion.div
            key={v.id}
            variants={row}
            className="flex items-start gap-3"
          >
            {/* Avatar */}
            <span className="shrink-0 size-9 rounded-full bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground">
              <Initials name={v.verifier_name} />
            </span>

            {/* Body */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-foreground truncate">
                  {v.verifier_name}
                </p>
                <RatingDots rating={v.rating} />
              </div>

              <div className="flex items-center gap-1.5 mt-0.5">
                {v.verifier_org && (
                  <span className="flex items-center gap-0.5 text-xs text-muted-foreground">
                    <Building2 className="size-3" aria-hidden="true" />
                    {v.verifier_org}
                  </span>
                )}
                <span className="text-xs text-muted-foreground">·</span>
                <span className="text-xs text-primary font-medium">{competencyLabel}</span>
                <span className="text-xs text-muted-foreground">·</span>
                <span className="text-xs text-muted-foreground">{date}</span>
              </div>

              {v.comment && (
                <p className="mt-1 text-xs text-muted-foreground italic leading-snug line-clamp-2">
                  &ldquo;{v.comment}&rdquo;
                </p>
              )}
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
