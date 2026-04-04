import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";
import "@/app/globals.css";
import i18nConfig from "@/i18nConfig";
import initTranslations from "@/app/i18n";
import TranslationsProvider from "@/components/translations-provider";
import { QueryProvider } from "@/components/query-provider";
import { UTMCapture } from "@/components/utm-capture";

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
  metadataBase: new URL(process.env.APP_URL || "http://localhost:3000"),
};

export const dynamic = "force-dynamic";

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
      <body className={`${inter.variable} ${plusJakartaSans.variable} font-sans`}>
        <TranslationsProvider
          locale={locale}
          namespaces={["common"]}
          resources={resources as import("i18next").Resource}
        >
          <QueryProvider>
            <UTMCapture />
            <div className="bg-primary/90 text-primary-foreground text-center text-xs py-1.5 px-4 font-medium sticky top-0 z-50">
              {locale === "az"
                ? "Bu platforma hazırda inkişaf mərhələsindədir. Bəzi funksiyalar hələ aktiv deyil."
                : "This platform is currently under development. Some features may not be available yet."}
            </div>
            {children}
          </QueryProvider>
        </TranslationsProvider>
      </body>
    </html>
  );
}
