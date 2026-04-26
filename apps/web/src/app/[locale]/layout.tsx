import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";
import "@/app/globals.css";
import i18nConfig from "@/i18nConfig";
import initTranslations from "@/app/i18n";
import TranslationsProvider from "@/components/translations-provider";
import { QueryProvider } from "@/components/query-provider";
import { UTMCapture } from "@/components/utm-capture";
import { PostHogProvider } from "@/components/posthog-provider";

const inter = Inter({ subsets: ["latin", "latin-ext"], variable: "--font-inter" });
const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-plus-jakarta-sans",
});

export const metadata: Metadata = {
  title: "Volaura — Verified Professional Talent Platform",
  description:
    "Prove your skills through adaptive assessment. Earn your AURA badge. Get discovered by top organizations.",
  metadataBase: new URL(process.env.APP_URL || "https://volaura.app"),
  openGraph: {
    title: "Volaura — Verified Professional Talent Platform",
    description:
      "Prove your skills through adaptive assessment. Earn your AURA badge. Get discovered by top organizations.",
    siteName: "Volaura",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Volaura — Verified Professional Talent Platform",
    description:
      "Prove your skills through adaptive assessment. Earn your AURA badge. Get discovered by top organizations.",
  },
  icons: {
    icon: "/icons/icon-192x192.png",
    apple: "/icons/icon-512x512.png",
  },
};

export function generateStaticParams() {
  return i18nConfig.locales.map((locale) => ({ locale }));
}

interface RootLayoutProps {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}

export default async function RootLayout({ children, params }: RootLayoutProps) {
  const { locale } = await params;
  const { resources } = await initTranslations(locale, ["common"]);

  return (
    <html lang={locale} className="dark" suppressHydrationWarning>
      <head>
        {/* One-time SW cache purge — forces browser to drop stale JS bundles */}
        <script dangerouslySetInnerHTML={{ __html: `
          if('serviceWorker' in navigator){
            navigator.serviceWorker.getRegistrations().then(function(regs){
              regs.forEach(function(r){r.unregister()});
            });
            caches.keys().then(function(names){
              names.forEach(function(n){caches.delete(n)});
            });
          }
        `}} />
      </head>
      <body className={`${inter.variable} ${plusJakartaSans.variable} font-sans`}>
        <TranslationsProvider
          locale={locale}
          namespaces={["common"]}
          resources={resources as import("i18next").Resource}
        >
          <QueryProvider>
            <PostHogProvider>
            <UTMCapture />
            <div className="bg-primary/90 text-primary-foreground text-center text-xs py-1.5 px-4 font-medium sticky top-0 z-50">
              {locale === "az"
                ? "Bu platforma hazırda inkişaf mərhələsindədir. Bəzi funksiyalar hələ aktiv deyil."
                : "This platform is currently under development. Some features may not be available yet."}
            </div>
            {children}
            </PostHogProvider>
          </QueryProvider>
        </TranslationsProvider>
      </body>
    </html>
  );
}
