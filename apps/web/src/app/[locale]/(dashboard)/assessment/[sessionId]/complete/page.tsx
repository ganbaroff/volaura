"use client";

import { useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { useAssessmentStore } from "@/stores/assessment-store";
import { Button } from "@/components/ui/button";
import { Loader2, Trophy } from "lucide-react";

interface PageProps {
  params: Promise<{ locale: string; sessionId: string }>;
}

export default function AssessmentCompletePage({ params }: PageProps) {
  const { locale } = use(params);
  const { t } = useTranslation();
  const router = useRouter();
  const { reset } = useAssessmentStore();

  // Clean up store state when arriving at complete screen
  useEffect(() => {
    reset();
  }, [reset]);

  const handleViewResults = () => {
    router.push(`/${locale}/aura`);
  };

  const handleRetake = () => {
    router.push(`/${locale}/assessment`);
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center text-center space-y-8">
      {/* Trophy animation */}
      <motion.div
        initial={{ scale: 0, rotate: -15 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 18, delay: 0.1 }}
      >
        <div className="size-24 rounded-full bg-primary/10 flex items-center justify-center">
          <Trophy className="size-12 text-primary" aria-hidden="true" />
        </div>
      </motion.div>

      {/* Copy */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="space-y-3"
      >
        <h1 className="text-2xl font-bold text-foreground">
          {t("assessment.complete")}
        </h1>
        <p className="text-sm text-muted-foreground max-w-xs mx-auto">
          {t("assessment.processingResults")}
        </p>
      </motion.div>

      {/* Processing indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="flex items-center gap-2 text-sm text-muted-foreground"
        role="status"
        aria-live="polite"
      >
        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
        <span>{t("assessment.processingResults")}</span>
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="flex flex-col gap-3 w-full"
      >
        <Button onClick={handleViewResults} size="lg" className="w-full">
          {t("assessment.viewResults")}
        </Button>
        <Button
          onClick={handleRetake}
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
        >
          {t("aura.retake")}
        </Button>
      </motion.div>
    </div>
  );
}
