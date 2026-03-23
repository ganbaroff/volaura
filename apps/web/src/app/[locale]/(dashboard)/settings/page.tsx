"use client";

import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";
import { LanguageSwitcher } from "@/components/layout/language-switcher";

export default function SettingsPage() {
  const { t } = useTranslation();

  return (
    <>
      <TopBar title={t("settings.title")} />
      <div className="mx-auto max-w-lg p-6 space-y-6">
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-4 text-base font-semibold">{t("settings.language")}</h2>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{t("settings.interfaceLanguage")}</p>
            <LanguageSwitcher />
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-2 text-base font-semibold">{t("settings.account")}</h2>
          <p className="text-sm text-muted-foreground">
            {t("settings.accountDescription")}
          </p>
        </section>
      </div>
    </>
  );
}
