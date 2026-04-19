import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.APP_URL || "https://volaura.app";

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/api/",
          "/admin/",
          "/callback/",
          "/*/sample",
          "/*/atlas",
          "/*/mindshift",
          "/*/brandedby",
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
