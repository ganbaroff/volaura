"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

export function SocialProof() {
  const { t } = useTranslation();
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://volauraapi-production.up.railway.app";
    fetch(`${API_URL}/api/stats/public`)
      .then((r) => r.json())
      .then((d) => setCount(d?.total_professionals ?? null))
      .catch(() => setCount(null));
  }, []);

  return (
    <section className="py-16 px-6" aria-label={t("landing.socialProofLabel", { defaultValue: "Community" })}>
      <div className="mx-auto max-w-2xl text-center space-y-6">
        <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          {t("landing.socialProofSubtitle", { defaultValue: "Built in Baku. For the world." })}
        </p>
        <p className="text-2xl sm:text-3xl font-bold text-foreground">
          {count !== null
            ? t("landing.socialProofCount", {
                count,
                defaultValue: `Join ${count} professionals already proving their skills`,
              })
            : t("landing.socialProofGeneric", {
                defaultValue: "Join professionals already proving their skills",
              })}
        </p>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          {t("landing.socialProofFounder", {
            defaultValue:
              "Founded by Yusif Ganbarov. One person, one vision: verified competency as the global standard for professional identity.",
          })}
        </p>
      </div>
    </section>
  );
}
