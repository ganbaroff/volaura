"use client";

import { notFound } from "next/navigation";
import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { useTranslation } from "react-i18next";

// Feature flag — off by default until ATLAS ships.
// Set NEXT_PUBLIC_ENABLE_ATLAS=true to expose the page.
const ATLAS_ENABLED = process.env.NEXT_PUBLIC_ENABLE_ATLAS === "true";

export default function AtlasPage() {
  if (!ATLAS_ENABLED) {
    notFound();
  }
  const { t } = useTranslation();
  return (
    <ProductPlaceholder
      name="ATLAS"
      icon="⚡"
      tagline={t("atlas.tagline", {
        defaultValue:
          "Coming after MindShift launch — ZEUS archived notice at memory/atlas/archive-notices/2026-04-19-zeus-frozen.md",
      })}
      accentVar="var(--color-product-atlas)"
    />
  );
}
