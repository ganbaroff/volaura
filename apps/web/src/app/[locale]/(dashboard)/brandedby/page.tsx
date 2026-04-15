"use client";

import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { useTranslation } from "react-i18next";

export default function BrandedByPage() {
  const { t } = useTranslation();
  return (
    <ProductPlaceholder
      name="BrandedBy"
      icon="✨"
      tagline={t("brandedby.tagline", {
        defaultValue: "AI Twin — your verified skills, in a talking-head video.",
      })}
      accentVar="var(--color-product-brandedby)"
    />
  );
}
