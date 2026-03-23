"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { ClipboardList, Award, Handshake } from "lucide-react";

const STEPS = [
  { num: 1, Icon: ClipboardList, color: "bg-blue-500" },
  { num: 2, Icon: Award, color: "bg-yellow-500" },
  { num: 3, Icon: Handshake, color: "bg-emerald-500" },
] as const;

export function HowItWorks() {
  const { t } = useTranslation();

  return (
    <section className="bg-muted/40 py-20 md:py-28">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("landing.howItWorksTitle")}
          </h2>
          <p className="text-lg text-muted-foreground">
            {t("landing.howItWorksSubtitle")}
          </p>
        </div>

        <div className="relative">
          {/* Connecting line (desktop only) */}
          <div
            className="absolute left-0 right-0 top-10 hidden h-px bg-border md:block"
            aria-hidden="true"
          />

          <div className="grid grid-cols-1 gap-10 md:grid-cols-3">
            {STEPS.map(({ num, Icon, color }, i) => (
              <motion.div
                key={num}
                className="flex flex-col items-center text-center"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
              >
                {/* Number circle */}
                <div
                  className={`relative z-10 mb-5 flex h-20 w-20 items-center justify-center rounded-full ${color} shadow-lg`}
                >
                  <Icon className="h-9 w-9 text-white" aria-hidden="true" />
                  <span className="absolute -right-1 -top-1 flex h-6 w-6 items-center justify-center rounded-full bg-background text-xs font-bold text-foreground ring-2 ring-border">
                    {num}
                  </span>
                </div>

                <h3 className="mb-2 text-lg font-semibold text-foreground">
                  {t(`landing.step${num}Title`)}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {t(`landing.step${num}Desc`)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
