import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";
import "@/app/globals.css";
import i18nConfig from "@/i18nConfig";
import initTranslations from "@/app/i18n";
import TranslationsProvider from "@/components/translations-provider";
import { QueryProvider } from "@/components/query-provider";

const inter = Inter({ subsets: ["latin", "latin-ext"], variable: "--font-inter" });
const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-plus-jakarta-sans",
});

export const metadata: Metadata = {
  title: "Volaura — Elite Volunteer Talent Platform",
  description:
    "Volaura is a verified volunteer talent platform. Get your AURA score, share your achievements, and connect with top event organizers.",
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
          <QueryProvider>{children}</QueryProvider>
        </TranslationsProvider>
      </body>
    </html>
  );
}
