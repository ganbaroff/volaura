"use client";

import { useTranslation } from "react-i18next";
import Link from "next/link";

interface LandingFooterProps {
  locale: string;
}

export function LandingFooter({ locale }: LandingFooterProps) {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-background py-12">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
          {/* Brand */}
          <div className="flex flex-col items-center gap-1 sm:items-start">
            <span className="text-lg font-extrabold tracking-tight text-foreground">
              Volaura
            </span>
            <span className="text-xs text-muted-foreground">
              {t("landing.footerTagline")}
            </span>
          </div>

          {/* Links */}
          <nav
            className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-muted-foreground"
            aria-label="Footer navigation"
          >
            <Link
              href={`/${locale}/events`}
              className="transition-colors hover:text-foreground"
            >
              {t("nav.events")}
            </Link>
            <Link
              href={`/${locale}/signup`}
              className="transition-colors hover:text-foreground"
            >
              {t("auth.signup")}
            </Link>
            <Link
              href={`/${locale}/login`}
              className="transition-colors hover:text-foreground"
            >
              {t("auth.login")}
            </Link>
          </nav>

          {/* Copyright */}
          <p className="text-xs text-muted-foreground">
            © {year} Volaura. {t("landing.footerRights")}
          </p>
        </div>
      </div>
    </footer>
  );
}
