"use client";

import { useTranslation } from "react-i18next";
import Link from "next/link";
import { cn } from "@/lib/utils/cn";

interface LandingNavProps {
  locale: string;
}

export function LandingNav({ locale }: LandingNavProps) {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link
          href={`/${locale}`}
          className="text-xl font-extrabold tracking-tight text-foreground"
          aria-label="Volaura home"
        >
          Volaura
        </Link>

        {/* Nav links */}
        <nav className="hidden items-center gap-6 sm:flex" aria-label="Main navigation">
          <Link
            href={`/${locale}/events`}
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            {t("nav.events")}
          </Link>
        </nav>

        {/* Auth buttons */}
        <div className="flex items-center gap-3">
          <Link
            href={`/${locale}/login`}
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            {t("auth.login")}
          </Link>
          <Link
            href={`/${locale}/signup`}
            className={cn(
              "rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground",
              "transition-colors hover:bg-primary/90",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            )}
          >
            {t("auth.signup")}
          </Link>
        </div>
      </div>
    </header>
  );
}
