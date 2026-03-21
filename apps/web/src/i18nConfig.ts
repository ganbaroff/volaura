const i18nConfig = {
  locales: ["en", "az"] as const,
  defaultLocale: "en" as const,
  prefixDefault: true,
};

export type Locale = (typeof i18nConfig)["locales"][number];

export default i18nConfig;
