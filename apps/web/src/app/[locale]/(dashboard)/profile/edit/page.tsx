"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ChevronLeft, Check } from "lucide-react";
import { TopBar } from "@/components/layout/top-bar";
import { useProfile, useUpdateProfile } from "@/hooks/queries/use-profile";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils/cn";

const LANGUAGE_OPTIONS = [
  { key: "Azerbaijani", labelKey: "onboarding.languageAzerbaijani" },
  { key: "English",     labelKey: "onboarding.languageEnglish" },
  { key: "Russian",     labelKey: "onboarding.languageRussian" },
  { key: "Turkish",     labelKey: "onboarding.languageTurkish" },
  { key: "Arabic",      labelKey: "onboarding.languageArabic" },
  { key: "Georgian",    labelKey: "onboarding.languageGeorgian" },
  { key: "Uzbek",       labelKey: "onboarding.languageUzbek" },
] as const;

function Toggle({
  id,
  checked,
  onChange,
}: {
  id: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        checked ? "bg-primary" : "bg-muted"
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "pointer-events-none inline-block size-5 rounded-full bg-white shadow-lg ring-0 transition-transform duration-200",
          checked ? "translate-x-5" : "translate-x-0"
        )}
      />
    </button>
  );
}

export default function EditProfilePage() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const { data: profile, isLoading, error } = useProfile();
  const updateProfile = useUpdateProfile();

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [location, setLocation] = useState("");
  const [languages, setLanguages] = useState<string[]>([]);
  const [isPublic, setIsPublic] = useState(true);
  const [visibleToOrgs, setVisibleToOrgs] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (!profile) return;
    setDisplayName(profile.display_name ?? "");
    setBio((profile as Record<string, unknown>).bio as string ?? "");
    setLocation(profile.location ?? "");
    setLanguages(profile.languages ?? []);
    setIsPublic((profile as Record<string, unknown>).is_public as boolean ?? true);
    setVisibleToOrgs((profile as Record<string, unknown>).visible_to_orgs as boolean ?? false);
  }, [profile]);

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [error, locale, router]);

  function toggleLanguage(key: string) {
    setLanguages((prev) =>
      prev.includes(key) ? prev.filter((l) => l !== key) : [...prev, key]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaveError(null);
    setSaved(false);

    try {
      await updateProfile.mutateAsync({
        display_name: displayName.trim() || null,
        bio: bio.trim() || null,
        location: location.trim() || null,
        languages: languages.length > 0 ? languages : null,
        is_public: isPublic,
        visible_to_orgs: visibleToOrgs,
      });
      if (!isMounted.current) return;
      setSaved(true);
      setTimeout(() => {
        if (isMounted.current) router.push(`/${locale}/profile`);
      }, 800);
    } catch (err) {
      if (!isMounted.current) return;
      setSaveError(err instanceof Error ? err.message : t("error.generic"));
    }
  }

  if (isLoading) {
    return (
      <>
        <TopBar title={t("profile.editProfile")} />
        <div className="p-4 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <TopBar title={t("profile.editProfile")} />

      <motion.form
        onSubmit={handleSubmit}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="p-4 space-y-5 pb-10"
      >
        {/* Back navigation */}
        <button
          type="button"
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground -ml-1 mb-1"
          aria-label={t("onboarding.back")}
        >
          <ChevronLeft className="size-4" aria-hidden="true" />
          {t("onboarding.back")}
        </button>
        <div className="space-y-1.5">
          <label htmlFor="display-name" className="text-sm font-medium text-foreground">
            {t("settings.displayName")}
          </label>
          <input
            id="display-name"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={80}
            placeholder={t("onboarding.namePlaceholder")}
            className="w-full rounded-xl border border-input bg-card px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="bio" className="text-sm font-medium text-foreground">
            {t("profile.edit.bio", { defaultValue: "About you" })}
          </label>
          <textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={300}
            rows={3}
            placeholder={t("profile.edit.bioPlaceholder", { defaultValue: "What do you do? What are you passionate about?" })}
            className="w-full rounded-xl border border-input bg-card px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 resize-none"
          />
          <p className="text-xs text-muted-foreground text-right">{bio.length}/300</p>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="location" className="text-sm font-medium text-foreground">
            {t("settings.location")}
          </label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            maxLength={100}
            placeholder={t("onboarding.locationPlaceholder")}
            className="w-full rounded-xl border border-input bg-card px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">{t("onboarding.languages")}</p>
          <div className="flex flex-wrap gap-2">
            {LANGUAGE_OPTIONS.map(({ key, labelKey }) => {
              const selected = languages.includes(key);
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggleLanguage(key)}
                  aria-pressed={selected}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-sm font-medium border transition-colors",
                    selected
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-card text-muted-foreground border-border hover:border-primary/50"
                  )}
                >
                  {t(labelKey)}
                </button>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card divide-y divide-border overflow-hidden">
          <div className="flex items-center justify-between gap-3 p-4">
            <div className="min-w-0">
              <label htmlFor="toggle-public" className="text-sm font-medium text-foreground">
                {t("profile.edit.publicProfile", { defaultValue: "Public profile" })}
              </label>
              <p className="text-xs text-muted-foreground mt-0.5">
                {t("profile.edit.publicProfileDesc", { defaultValue: "Anyone with your link can view your profile" })}
              </p>
            </div>
            <Toggle id="toggle-public" checked={isPublic} onChange={setIsPublic} />
          </div>

          <div className="flex items-center justify-between gap-3 p-4">
            <div className="min-w-0">
              <label htmlFor="toggle-orgs" className="text-sm font-medium text-foreground">
                {t("profile.edit.discoverableLabel", { defaultValue: "Discoverable by organizations" })}
              </label>
              <p className="text-xs text-muted-foreground mt-0.5">
                {t("profile.edit.discoverableDesc", { defaultValue: "Organizations can find you in search" })}
              </p>
            </div>
            <Toggle id="toggle-orgs" checked={visibleToOrgs} onChange={setVisibleToOrgs} />
          </div>
        </div>

        {saveError && (
          <p role="alert" className="text-sm text-destructive">{saveError}</p>
        )}

        <button
          type="submit"
          disabled={updateProfile.isPending || saved}
          className={cn(
            "w-full flex items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold transition-colors",
            saved
              ? "bg-green-600 text-white"
              : "bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          )}
        >
          {saved ? (
            <><Check className="size-4" aria-hidden="true" />{t("settings.saved")}</>
          ) : updateProfile.isPending ? (
            t("onboarding.saving")
          ) : (
            t("settings.saveChanges")
          )}
        </button>
      </motion.form>
    </>
  );
}
