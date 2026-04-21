"use client";

import { notFound } from "next/navigation";
import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { useTranslation } from "react-i18next";

// Feature flag — off by default until BrandedBy ships.
// Set NEXT_PUBLIC_ENABLE_BRANDEDBY=true to expose the page.
const BRANDEDBY_ENABLED = process.env.NEXT_PUBLIC_ENABLE_BRANDEDBY === "true";

export default function BrandedByPage() {
  if (!BRANDEDBY_ENABLED) {
    notFound();
  }
  const { t } = useTranslation();
  return (
    <ProductPlaceholder
      name="BrandedBy"
      icon="✨"
      tagline={t("brandedby.tagline", {
        defaultValue:
          "Coming after MindShift launch — archived notice at memory/atlas/archive-notices/2026-04-19-brandedby-frozen.md",
      })}
      accentVar="var(--color-product-brandedby)"
    />
  );
}
