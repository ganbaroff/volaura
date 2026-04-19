"use client";

import { notFound } from "next/navigation";
import { ProductPlaceholder } from "@/components/ui/product-placeholder";
import { useTranslation } from "react-i18next";

// Feature flag — off by default until MindShift ships.
// Set NEXT_PUBLIC_ENABLE_MINDSHIFT=true to expose the page.
const MINDSHIFT_ENABLED = process.env.NEXT_PUBLIC_ENABLE_MINDSHIFT === "true";

export default function MindShiftPage() {
  if (!MINDSHIFT_ENABLED) {
    notFound();
  }
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
