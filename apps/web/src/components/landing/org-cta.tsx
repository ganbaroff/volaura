"use client";

import { useTranslation } from "react-i18next";
import Link from "next/link";
import { motion } from "framer-motion";
import { Building2, ArrowRight } from "lucide-react";

interface OrgCtaProps {
  locale: string;
}

export function OrgCta({ locale }: OrgCtaProps) {
  const { t } = useTranslation();

  return (
    <section className="py-20 md:py-28">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <motion.div
          className="overflow-hidden rounded-3xl bg-primary p-10 text-center shadow-xl md:p-14"
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <div className="mb-5 flex justify-center">
            <div className="rounded-2xl bg-white/20 p-4">
              <Building2 className="h-8 w-8 text-white" aria-hidden="true" />
            </div>
          </div>

          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            {t("landing.orgTitle")}
          </h2>
          <p className="mb-8 text-lg text-white/80">
            {t("landing.orgSubtitle")}
          </p>

          <Link
            href={`/${locale}/signup`}
            className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-primary shadow-md transition-all hover:bg-white/90 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            {t("landing.orgCta")}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
