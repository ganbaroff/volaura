"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import {
  Target,
  Users,
  CalendarCheck,
  Trophy,
  Lightbulb,
  ArrowRight,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

// ── Types matching feed-curator skill output ──

export type FeedCardType = "challenge" | "people" | "event" | "achievement" | "insight";

export interface FeedCard {
  type: FeedCardType;
  title: string;
  description: string;
  cta?: string;
  priority?: number;
  relevance_reason?: string;
  match_score?: number;
  match_reason?: string;
  celebration_level?: "small" | "medium" | "big";
  source?: string;
  relevance?: string;
}

interface FeedCardsProps {
  cards: FeedCard[];
  loading?: boolean;
  locale: string;
  onCardAction?: (card: FeedCard) => void;
}

const CARD_CONFIG: Record<FeedCardType, {
  icon: typeof Target;
  accent: string;
  bg: string;
}> = {
  challenge:   { icon: Target,        accent: "text-amber-600",  bg: "bg-amber-50 dark:bg-amber-950/30" },
  people:      { icon: Users,         accent: "text-blue-600",   bg: "bg-blue-50 dark:bg-blue-950/30" },
  event:       { icon: CalendarCheck, accent: "text-green-600",  bg: "bg-green-50 dark:bg-green-950/30" },
  achievement: { icon: Trophy,        accent: "text-purple-600", bg: "bg-purple-50 dark:bg-purple-950/30" },
  insight:     { icon: Lightbulb,     accent: "text-cyan-600",   bg: "bg-cyan-50 dark:bg-cyan-950/30" },
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const cardAnim = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" as const } },
};

export function FeedCards({ cards, loading, locale, onCardAction }: FeedCardsProps) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!cards || cards.length === 0) {
    return (
      <div className="py-4 text-center space-y-3">
        <Lightbulb className="mx-auto size-8 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">
          {t("dashboard.feed.empty", { defaultValue: "Complete an assessment to unlock personalized recommendations" })}
        </p>
        <Link
          href={`/${locale}/assessment`}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          {t("dashboard.feed.emptyAction", { defaultValue: "Take your first assessment" })}
          <ArrowRight className="size-3.5" />
        </Link>
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
      {cards.slice(0, 7).map((card, idx) => {
        const config = CARD_CONFIG[card.type] ?? CARD_CONFIG.insight;
        const Icon = config.icon;

        return (
          <motion.div
            key={`${card.type}-${idx}`}
            variants={cardAnim}
            className={cn(
              "rounded-xl border p-4 transition-colors",
              config.bg,
              onCardAction && "cursor-pointer hover:border-primary/30",
              card.type === "achievement" && card.celebration_level === "big" && "ring-2 ring-purple-300/50",
            )}
            onClick={() => onCardAction?.(card)}
            role={onCardAction ? "button" : undefined}
            tabIndex={onCardAction ? 0 : undefined}
            onKeyDown={(e) => e.key === "Enter" && onCardAction?.(card)}
          >
            <div className="flex items-start gap-3">
              <span className={cn("shrink-0 mt-0.5", config.accent)}>
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <div className="flex-1 min-w-0">
                <p className={cn("text-sm font-semibold", config.accent)}>
                  {card.title}
                </p>
                <p className="text-sm text-foreground/80 mt-1 leading-relaxed">
                  {card.description}
                </p>
                {card.relevance_reason && (
                  <p className="text-xs text-muted-foreground mt-1.5 italic">
                    {card.relevance_reason}
                  </p>
                )}
                {card.match_reason && (
                  <p className="text-xs text-muted-foreground mt-1.5 italic">
                    {card.match_reason}
                  </p>
                )}
              </div>
              {card.cta && onCardAction && (
                <ArrowRight className="size-4 text-muted-foreground shrink-0 mt-1" />
              )}
            </div>
            {card.cta && (
              <div className="mt-3 ml-8">
                <span className={cn("text-xs font-medium", config.accent)}>
                  {card.cta}
                </span>
              </div>
            )}
          </motion.div>
        );
      })}
    </motion.div>
  );
}
