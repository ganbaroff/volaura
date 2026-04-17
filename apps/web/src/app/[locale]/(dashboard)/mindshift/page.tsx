"use client";

import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { useTranslation } from "react-i18next";

export default function MindShiftPage() {
  const { t } = useTranslation();
  return (
    <ProductPlaceholder
      name="MindShift"
      icon="🧠"
      tagline={t("mindshift.tagline", {
        defaultValue: "AI-powered cognitive training. Sharpen focus, build mental resilience.",
      })}
      accentVar="var(--color-product-mindshift)"
    />
  );
}
