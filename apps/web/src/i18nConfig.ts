const i18nConfig = {
  locales: ["az", "en"] as const,
  defaultLocale: "az" as const,
  prefixDefault: true,
};

export type Locale = (typeof i18nConfig)["locales"][number];

export default i18nConfig;
