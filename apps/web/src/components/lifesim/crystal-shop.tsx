"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import {
  Briefcase,
  Coins,
  HeartPulse,
  PartyPopper,
  BookOpen,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils/cn";
import { useLifesimPurchase } from "@/hooks/queries/use-lifesim";

/**
 * Crystal Shop — 4 items hardcoded per LIFE-SIMULATOR-GAME-DESIGN.md §Crystal Economy.
 *
 * Sprint A8. Confirm dialog + POST /api/lifesim/purchase wiring + stat-boost
 * callback for optimistic local-stat application.
 *
 * Item IDs MUST match the backend _CRYSTAL_SHOP dict in apps/api/app/routers/lifesim.py
 * or the purchase endpoint returns 404. Keeping catalogue inline for MVP; future
 * iteration promotes to a lifesim_shop_items DB table.
 */

export interface ShopItem {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  cost: number;
  boostDescription: string;
  // The stat-boost callback applies these deltas to the local Life Feed stats
  boost: Record<string, number>;
}

export const SHOP_ITEMS: ShopItem[] = [
  {
    id: "premium_training_course",
    icon: BookOpen,
    cost: 50,
    boostDescription: "intelligence +10",
    boost: { intelligence: 10 },
  },
  {
    id: "social_event_ticket",
    icon: PartyPopper,
    cost: 30,
    boostDescription: "social +5 · happiness +5",
    boost: { social: 5, happiness: 5 },
  },
  {
    id: "health_insurance",
    icon: HeartPulse,
    cost: 100,
    boostDescription: "health +10",
    boost: { health: 10 },
  },
  {
    id: "career_coach",
    icon: Briefcase,
    cost: 75,
    boostDescription: "next promotion guaranteed",
    boost: { career_bonus_flag: 1 },
  },
];

interface CrystalShopProps {
  currentCrystals: number;
  onBoost: (boost: Record<string, number>) => void;
}

export function CrystalShop({ currentCrystals, onBoost }: CrystalShopProps) {
  const { t } = useTranslation();
  const purchaseMutation = useLifesimPurchase();
  const [pendingItem, setPendingItem] = useState<ShopItem | null>(null);

  const handleConfirm = async () => {
    if (!pendingItem) return;
    try {
      await purchaseMutation.mutateAsync({
        shop_item: pendingItem.id,
        current_crystals: currentCrystals,
      });
      onBoost(pendingItem.boost);
    } catch {
      // Error state lives in mutation.isError; UI surfaces inline
    } finally {
      setPendingItem(null);
    }
  };

  return (
    <>
      <section
        className="mt-8 rounded-xl border border-border bg-card p-5 md:p-6"
        aria-label={t("lifesim.shop.title", { defaultValue: "Crystal Shop" })}
      >
        <header className="flex items-center justify-between gap-3 mb-5">
          <div className="flex items-center gap-2">
            <Coins className="size-5 text-primary" aria-hidden="true" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              {t("lifesim.shop.title", { defaultValue: "Crystal Shop" })}
            </h2>
          </div>
          <span className="text-xs font-medium text-muted-foreground tabular-nums">
            {t("lifesim.shop.balance", {
              defaultValue: "Balance: {{count}}",
              count: currentCrystals,
            })}
          </span>
        </header>

        <div className="grid gap-3 sm:grid-cols-2">
          {SHOP_ITEMS.map((item) => {
            const Icon = item.icon;
            const canAfford = currentCrystals >= item.cost;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setPendingItem(item)}
                disabled={!canAfford || purchaseMutation.isPending}
                className={cn(
                  "text-left rounded-lg border border-border bg-surface-container-low p-4",
                  "flex items-start gap-3",
                  "hover:border-primary/60 hover:bg-surface-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
                  "transition-colors duration-200",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-surface-container-low"
                )}
                aria-label={t(`lifesim.shop.item.${item.id}.name`, {
                  defaultValue: item.id,
                })}
              >
                <Icon className="size-6 shrink-0 text-primary mt-0.5" aria-hidden="true" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2 mb-1">
                    <span className="text-sm font-semibold text-foreground">
                      {t(`lifesim.shop.item.${item.id}.name`, {
                        defaultValue: item.id.replace(/_/g, " "),
                      })}
                    </span>
                    <span className="text-xs font-bold text-primary tabular-nums">
                      {item.cost} ♦
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{item.boostDescription}</p>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <AnimatePresence>
        {pendingItem ? (
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="shop-confirm-title"
            onClick={() => setPendingItem(null)}
          >
            <motion.div
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.97 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl"
            >
              <div className="flex items-start justify-between mb-4">
                <h3
                  id="shop-confirm-title"
                  className="text-lg font-headline font-bold text-foreground"
                >
                  {t("lifesim.shop.confirm.title", { defaultValue: "Подтвердить покупку?" })}
                </h3>
                <button
                  type="button"
                  onClick={() => setPendingItem(null)}
                  className="shrink-0 size-7 rounded-full flex items-center justify-center text-muted-foreground hover:bg-surface-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                  aria-label={t("common.close", { defaultValue: "Close" })}
                >
                  <X className="size-4" aria-hidden="true" />
                </button>
              </div>

              <p className="text-sm text-on-surface-variant mb-1">
                {t(`lifesim.shop.item.${pendingItem.id}.name`, {
                  defaultValue: pendingItem.id.replace(/_/g, " "),
                })}
              </p>
              <p className="text-xs text-muted-foreground mb-4">{pendingItem.boostDescription}</p>

              <div className="flex items-baseline justify-between mb-5 py-3 px-4 rounded-lg bg-surface-container-low">
                <span className="text-xs font-medium text-muted-foreground">
                  {t("lifesim.shop.confirm.cost", { defaultValue: "Cost" })}
                </span>
                <span className="text-base font-bold text-primary tabular-nums">
                  {pendingItem.cost} ♦
                </span>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setPendingItem(null)}
                  disabled={purchaseMutation.isPending}
                  className={cn(
                    "flex-1 rounded-lg border border-border bg-surface-container-low px-4 py-2.5",
                    "text-sm font-medium text-foreground",
                    "hover:bg-surface-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
                    "transition-colors duration-200",
                    "disabled:opacity-60"
                  )}
                >
                  {t("common.cancel", { defaultValue: "Cancel" })}
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={purchaseMutation.isPending || currentCrystals < pendingItem.cost}
                  className={cn(
                    "flex-1 rounded-lg bg-primary px-4 py-2.5",
                    "text-sm font-semibold text-primary-foreground",
                    "hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
                    "transition-colors duration-200",
                    "disabled:opacity-60 disabled:cursor-not-allowed"
                  )}
                >
                  {purchaseMutation.isPending
                    ? t("common.loading", { defaultValue: "Loading…" })
                    : t("lifesim.shop.confirm.cta", { defaultValue: "Подтвердить" })}
                </button>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
