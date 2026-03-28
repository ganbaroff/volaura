"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { useProfile, useUpdateProfile } from "@/hooks/queries";
import { useAuthToken } from "@/hooks/queries";
import { apiFetch } from "@/lib/api/client";
import { createClient } from "@/lib/supabase/client";

type VisibilityOption = "public" | "badge_only" | "hidden";

export default function SettingsPage() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const getToken = useAuthToken();

  // Profile section state
  const { data: profile, isLoading: profileLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const [displayName, setDisplayName] = useState("");
  const [location, setLocation] = useState("");
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  // AURA visibility state
  const [visibility, setVisibility] = useState<VisibilityOption>("public");
  const [visibilitySaved, setVisibilitySaved] = useState(false);
  const [visibilityError, setVisibilityError] = useState<string | null>(null);
  const [visibilityLoading, setVisibilityLoading] = useState(false);

  // Sign out state
  const [signingOut, setSigningOut] = useState(false);

  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Seed form fields when profile loads
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name ?? "");
      setLocation(profile.location ?? "");
    }
  }, [profile]);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileError(null);
    setProfileSaved(false);

    try {
      await updateProfile.mutateAsync({
        display_name: displayName || null,
        location: location || null,
      });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : t("error.generic"));
    }
  }

  async function handleSaveVisibility(e: React.FormEvent) {
    e.preventDefault();
    setVisibilityError(null);
    setVisibilitySaved(false);
    setVisibilityLoading(true);

    try {
      const token = await getToken();
      if (!token) {
        setVisibilityError(t("error.unauthorized"));
        return;
      }
      await apiFetch("/api/aura/me/visibility", {
        method: "PATCH",
        token,
        body: JSON.stringify({ visibility }),
      });
      setVisibilitySaved(true);
      setTimeout(() => setVisibilitySaved(false), 3000);
    } catch (err) {
      setVisibilityError(err instanceof Error ? err.message : t("error.generic"));
    } finally {
      setVisibilityLoading(false);
    }
  }

  async function handleSignOut() {
    setSigningOut(true);
    try {
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push(`/${locale}/login`);
    } catch {
      setSigningOut(false);
    }
  }

  async function handleDeleteAccount() {
    if (deleteConfirmText !== "DELETE") return;
    setDeleting(true);
    setDeleteError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error(t("error.unauthorized"));
      await apiFetch("/api/auth/me", { method: "DELETE", token });
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push(`/${locale}/login`);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : t("error.generic"));
      setDeleting(false);
    }
  }

  return (
    <>
      <TopBar title={t("settings.title")} />
      <div className="mx-auto max-w-lg p-6 space-y-6">

        {/* Account Section */}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-4 text-base font-semibold">{t("settings.account")}</h2>
          {profileLoading ? (
            <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
          ) : (
            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="displayName" className="text-sm font-medium">
                  {t("settings.displayName")}
                </label>
                <input
                  id="displayName"
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="username" className="text-sm font-medium">
                  {t("settings.username")}
                </label>
                <div className="flex h-10 w-full items-center rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground">
                  @{profile?.username ?? ""}
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="location" className="text-sm font-medium">
                  {t("settings.location")}
                </label>
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                />
              </div>

              {profileError && (
                <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {profileError}
                </p>
              )}

              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={updateProfile.isPending}
                  className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  {updateProfile.isPending ? t("loading.saving") : t("settings.saveChanges")}
                </button>
                {profileSaved && (
                  <span className="text-sm text-green-500">{t("settings.saved")}</span>
                )}
              </div>
            </form>
          )}
        </section>

        {/* AURA Privacy Section */}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-base font-semibold">{t("settings.privacy")}</h2>
          <p className="mb-4 text-sm text-muted-foreground">{t("settings.visibility")}</p>
          <form onSubmit={handleSaveVisibility} className="space-y-3">
            {(
              [
                { value: "public", label: t("settings.visibilityPublic") },
                { value: "badge_only", label: t("settings.visibilityBadgeOnly") },
                { value: "hidden", label: t("settings.visibilityHidden") },
              ] as { value: VisibilityOption; label: string }[]
            ).map((option) => (
              <label
                key={option.value}
                className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                  visibility === option.value
                    ? "border-primary bg-primary/5"
                    : "border-border"
                }`}
              >
                <input
                  type="radio"
                  name="visibility"
                  value={option.value}
                  checked={visibility === option.value}
                  onChange={() => setVisibility(option.value)}
                  className="accent-primary"
                />
                <span className="text-sm">{option.label}</span>
              </label>
            ))}

            {visibilityError && (
              <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {visibilityError}
              </p>
            )}

            <div className="flex items-center gap-3 pt-1">
              <button
                type="submit"
                disabled={visibilityLoading}
                className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
              >
                {visibilityLoading ? t("loading.saving") : t("settings.saveChanges")}
              </button>
              {visibilitySaved && (
                <span className="text-sm text-green-500">{t("settings.saved")}</span>
              )}
            </div>
          </form>
        </section>

        {/* Language Section */}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-4 text-base font-semibold">{t("settings.language")}</h2>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{t("settings.interfaceLanguage")}</p>
            <LanguageSwitcher />
          </div>
        </section>

        {/* Account Actions / Danger Zone */}
        <section className="rounded-xl border border-destructive/30 bg-card p-5 space-y-4">
          <h2 className="text-base font-semibold text-destructive">
            {t("settings.dangerZone")}
          </h2>

          {/* Sign out */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{t("settings.signOutDesc", { defaultValue: "Sign out of your account" })}</p>
            <button
              type="button"
              onClick={handleSignOut}
              disabled={signingOut}
              className="h-9 rounded-md border border-destructive px-3 text-sm font-medium text-destructive transition-colors hover:bg-destructive hover:text-destructive-foreground disabled:opacity-50"
            >
              {signingOut ? t("loading.saving") : t("settings.signOut")}
            </button>
          </div>

          {/* Delete account */}
          <div className="border-t border-destructive/20 pt-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-destructive">{t("settings.deleteAccount", { defaultValue: "Delete Account" })}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{t("settings.deleteAccountDesc", { defaultValue: "Permanently delete your account and all data. This cannot be undone." })}</p>
              </div>
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="shrink-0 h-9 rounded-md bg-destructive/10 border border-destructive/30 px-3 text-sm font-medium text-destructive transition-colors hover:bg-destructive hover:text-destructive-foreground"
              >
                {t("settings.deleteAccount", { defaultValue: "Delete" })}
              </button>
            </div>
          </div>
        </section>

        {/* Delete confirmation modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
            <div className="w-full max-w-sm rounded-2xl border border-destructive/30 bg-card p-6 space-y-4 shadow-2xl">
              <h3 className="text-lg font-bold text-destructive">
                {t("settings.deleteAccountConfirmTitle", { defaultValue: "Delete account permanently?" })}
              </h3>
              <p className="text-sm text-muted-foreground">
                {t("settings.deleteAccountConfirmDesc", { defaultValue: 'This will permanently delete your AURA score, assessments, and profile. Type "DELETE" to confirm.' })}
              </p>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE"
                className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-destructive/40"
                aria-label={t("settings.typeDelete", { defaultValue: 'Type DELETE to confirm' })}
              />
              {deleteError && (
                <p className="rounded-md bg-destructive/10 p-2 text-xs text-destructive">{deleteError}</p>
              )}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => { setShowDeleteConfirm(false); setDeleteConfirmText(""); setDeleteError(null); }}
                  className="flex-1 h-10 rounded-md border border-border text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
                >
                  {t("common.cancel", { defaultValue: "Cancel" })}
                </button>
                <button
                  type="button"
                  onClick={handleDeleteAccount}
                  disabled={deleteConfirmText !== "DELETE" || deleting}
                  className="flex-1 h-10 rounded-md bg-destructive text-sm font-medium text-destructive-foreground disabled:opacity-40 hover:bg-destructive/90 transition-colors"
                >
                  {deleting ? t("loading.saving") : t("settings.deleteAccount", { defaultValue: "Delete Forever" })}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </>
  );
}
