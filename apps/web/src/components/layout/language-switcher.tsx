"use client";

import { usePathname, useRouter } from "next/navigation";
import i18nConfig, { type Locale } from "@/i18nConfig";

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();

  const currentLocale = (i18nConfig.locales.find((l) => pathname.startsWith(`/${l}/`) || pathname === `/${l}`) ??
    i18nConfig.defaultLocale) as Locale;

  function switchLocale(newLocale: Locale) {
    if (newLocale === currentLocale) return;
    const segments = pathname.split("/");
    segments[1] = newLocale;
    const newPath = segments.join("/") || "/";
    router.push(newPath.startsWith("/") ? newPath : `/${newPath}`);
  }

  return (
    <div className="flex items-center gap-1 rounded-full bg-surface-container-high p-1">
      {i18nConfig.locales.map((locale) => (
        <button
          key={locale}
          onClick={() => switchLocale(locale as Locale)}
          className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide transition-all ${
            locale === currentLocale
              ? "bg-primary text-on-primary shadow-[0_0_8px_rgba(192,193,255,0.3)]"
              : "text-on-surface-variant hover:text-on-surface"
          }`}
        >
          {locale}
        </button>
      ))}
    </div>
  );
}
