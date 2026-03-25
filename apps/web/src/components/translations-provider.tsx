"use client";

import { I18nextProvider } from "react-i18next";
import { createInstance, type Resource } from "i18next";
import resourcesToBackend from "i18next-resources-to-backend";
import { initReactI18next } from "react-i18next/initReactI18next";
import i18nConfig from "@/i18nConfig";

interface TranslationsProviderProps {
  children: React.ReactNode;
  locale: string;
  namespaces: string[];
  resources: Resource;
}

export default function TranslationsProvider({
  children,
  locale,
  namespaces,
  resources,
}: TranslationsProviderProps) {
  const i18n = createInstance();

  i18n
    .use(initReactI18next)
    .use(
      resourcesToBackend(
        (language: string, namespace: string) =>
          import(`@/locales/${language}/${namespace}.json`)
      )
    )
    .init({
      lng: locale,
      fallbackLng: i18nConfig.defaultLocale,
      supportedLngs: i18nConfig.locales,
      defaultNS: namespaces[0],
      fallbackNS: namespaces[0],
      ns: namespaces,
      resources,
      // Required: makes initialization synchronous when resources are pre-loaded.
      // Without this, i18next async-inits even with resources provided, causing
      // t() to return keys on the first render → hydration mismatch (React #425).
      initImmediate: false,
    });

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}
