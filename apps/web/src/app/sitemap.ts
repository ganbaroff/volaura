import type { MetadataRoute } from "next";

const BASE_URL = process.env.APP_URL || "https://volaura.app";
const LOCALES = ["az", "en"] as const;

function localeUrls(
  path: string,
  opts?: { priority?: number; changeFrequency?: MetadataRoute.Sitemap[number]["changeFrequency"] },
): MetadataRoute.Sitemap {
  return LOCALES.map((locale) => ({
    url: `${BASE_URL}/${locale}${path}`,
    lastModified: new Date(),
    changeFrequency: opts?.changeFrequency ?? "weekly",
    priority: opts?.priority ?? 0.5,
  }));
}

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    ...localeUrls("", { priority: 1.0, changeFrequency: "daily" }),
    ...localeUrls("/welcome", { priority: 0.8 }),
    ...localeUrls("/events", { priority: 0.7, changeFrequency: "daily" }),
    ...localeUrls("/organizations", { priority: 0.7, changeFrequency: "daily" }),
    ...localeUrls("/privacy", { priority: 0.3, changeFrequency: "monthly" }),
    ...localeUrls("/terms", { priority: 0.3, changeFrequency: "monthly" }),
    ...localeUrls("/login", { priority: 0.6 }),
    ...localeUrls("/signup", { priority: 0.6 }),
  ];
}
