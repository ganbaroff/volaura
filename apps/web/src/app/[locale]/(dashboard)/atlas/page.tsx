"use client";

import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { useTranslation } from "react-i18next";

export default function AtlasPage() {
  const { t } = useTranslation();
  return (
    <ProductPlaceholder
      name="ATLAS"
      icon="⚡"
      tagline={t("atlas.tagline", {
        defaultValue: "The orchestrator. One gateway to manage all ecosystem products.",
      })}
      accentVar="var(--color-product-atlas)"
    />
  );
}
