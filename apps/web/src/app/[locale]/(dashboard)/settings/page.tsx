"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { useProfile, useUpdateProfile, useSubscription } from "@/hooks/queries";
import { useAuthToken } from "@/hooks/queries";
import { apiFetch } from "@/lib/api/client";
import { createClient } from "@/lib/supabase/client";
import { EnergyPicker } from "@/components/assessment/energy-picker";
import { useEnergyMode } from "@/hooks/use-energy-mode";

type VisibilityOption = "public" | "badge_only" | "hidden";

export default function SettingsPage() {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const getToken = useAuthToken();

  // Subscription
  const { status: subStatus, daysRemaining, isTrial, isExpired, trialEndsAt, subscriptionEndsAt, isLoading: subLoading } = useSubscription();
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);

  // Profile section state
  const { data: profile, isLoading: profileLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const [displayName, setDisplayName] = useState("");
  const [location, setLocation] = useState("");
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  // AURA visibility state — seeded from API, not hardcoded to "public"
  const [visibility, setVisibility] = useState<VisibilityOption>("public");
  const [visibilityFetched, setVisibilityFetched] = useState(false);
  const [visibilitySaved, setVisibilitySaved] = useState(false);
  const [visibilityError, setVisibilityError] = useState<string | null>(null);
  const [visibilityLoading, setVisibilityLoading] = useState(false);

  // Talent search opt-in state (visible_to_orgs)
  const [visibleToOrgs, setVisibleToOrgs] = useState(false);
  const [orgVisibilitySaved, setOrgVisibilitySaved] = useState(false);
  const [orgVisibilityError, setOrgVisibilityError] = useState<string | null>(null);
  const [orgVisibilityLoading, setOrgVisibilityLoading] = useState(false);

  // Energy mode (Constitution Law 2)
  const { energy, setEnergy } = useEnergyMode();

  // Sign out state
  const [signingOut, setSigningOut] = useState(false);

  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Seed form fields when profile loads (including visible_to_orgs)
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name ?? "");
      setLocation(profile.location ?? "");
      setVisibleToOrgs((profile as Record<string, unknown>).visible_to_orgs as boolean ?? false);
    }
  }, [profile]);

  // Fetch current AURA visibility from API — prevents silent override (Leyla simulation P0)
  useEffect(() => {
    if (visibilityFetched) return;
    getToken().then(async (token) => {
      if (!token) return;
      try {
        const res = await apiFetch<{ visibility: VisibilityOption }>("/api/aura/me/visibility", { token });
        if (res?.visibility) {
          setVisibility(res.visibility);
        }
      } catch {
        // Not critical — defaults to "public" if fetch fails (user can still save)
      } finally {
        setVisibilityFetched(true);
      }
    });
  }, [getToken, visibilityFetched]);

  async function handleSubscribeClick() {
    setCheckoutError(null);
    setCheckoutLoading(true);
    try {
      const token = await getToken();
      if (!token) { setCheckoutError(t("error.unauthorized")); return; }
      const res = await apiFetch<{ checkout_url: string }>("/api/subscription/create-checkout", {
        method: "POST",
        token,
      });
      if (res?.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status;
      if (status === 503) {
        setCheckoutError(t("subscription.setupInProgress", "Subscription setup in progress — contact us to upgrade early."));
      } else {
        setCheckoutError(t("subscription.checkoutError", "Could not start checkout — please try again."));
      }
    } finally {
      setCheckoutLoading(false);
    }
  }

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
      await apiFetch("/aura/me/visibility", {
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

  async function handleSaveOrgVisibility(e: React.FormEvent) {
    e.preventDefault();
    setOrgVisibilityError(null);
    setOrgVisibilitySaved(false);
    setOrgVisibilityLoading(true);
    try {
      await updateProfile.mutateAsync({ visible_to_orgs: visibleToOrgs } as Parameters<typeof updateProfile.mutateAsync>[0]);
      setOrgVisibilitySaved(true);
      setTimeout(() => setOrgVisibilitySaved(false), 3000);
    } catch (err) {
      setOrgVisibilityError(err instanceof Error ? err.message : t("error.generic"));
    } finally {
      setOrgVisibilityLoading(false);
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
      await apiFetch("/auth/me", { method: "DELETE", token });
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
                <p className="rounded-md bg-error-container p-3 text-sm text-on-error-container">
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
              <p className="rounded-md bg-error-container p-3 text-sm text-on-error-container">
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

        {/* Talent Search Visibility (visible_to_orgs) — Leyla simulation P0: was only settable at onboarding */}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-base font-semibold">
            {t("settings.talentSearch", { defaultValue: "Talent Search" })}
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">
            {t("settings.talentSearchDesc", { defaultValue: "Control whether organizations can find you in their talent search." })}
          </p>
          <form onSubmit={handleSaveOrgVisibility} className="space-y-3">
            <label className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${visibleToOrgs ? "border-primary bg-primary/5" : "border-border"}`}>
              <input
                type="checkbox"
                checked={visibleToOrgs}
                onChange={(e) => setVisibleToOrgs(e.target.checked)}
                className="accent-primary h-4 w-4"
              />
              <div>
                <span className="text-sm font-medium">
                  {t("settings.visibleToOrgs", { defaultValue: "Appear in organization talent search" })}
                </span>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {t("settings.visibleToOrgsDesc", { defaultValue: "Organizations can find your profile and send introduction requests." })}
                </p>
              </div>
            </label>

            {orgVisibilityError && (
              <p className="rounded-md bg-error-container p-3 text-sm text-on-error-container">
                {orgVisibilityError}
              </p>
            )}

            <div className="flex items-center gap-3 pt-1">
              <button
                type="submit"
                disabled={orgVisibilityLoading}
                className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
              >
                {orgVisibilityLoading ? t("loading.saving") : t("settings.saveChanges")}
              </button>
              {orgVisibilitySaved && (
                <span className="text-sm text-green-500">{t("settings.saved")}</span>
              )}
            </div>
          </form>
        </section>

        {/* Energy Mode — Constitution Law 2 */}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-base font-semibold font-headline">
            {t("settings.energyMode", { defaultValue: "Energy Mode" })}
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">
            {t("settings.energyModeDesc", { defaultValue: "Adjust spacing, animations, and density to match your energy level." })}
          </p>
          <EnergyPicker value={energy} onChange={setEnergy} />
        </section>

        {/* Language Section */}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-4 text-base font-semibold font-headline">{t("settings.language")}</h2>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{t("settings.interfaceLanguage")}</p>
            <LanguageSwitcher />
          </div>
        </section>

        {/* Subscription Section */}
        <section className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h2 className="text-base font-semibold">{t("subscription.currentPlan")}</h2>

          {subLoading ? (
            <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
          ) : (
            <div className="space-y-3">
              {/* Plan badge */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{t("subscription.currentPlan")}</span>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    isExpired
                      ? "bg-destructive/10 text-destructive"
                      : isTrial
                      ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200"
                      : "bg-primary/10 text-primary"
                  }`}
                >
                  {subStatus ? t(`subscription.${subStatus}`) : "—"}
                </span>
              </div>

              {/* Days remaining */}
              {(isTrial || subStatus === "active") && daysRemaining !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    {isTrial ? t("subscription.trialEndDate") : t("subscription.renewsOn")}
                  </span>
                  <span className="text-sm font-medium">
                    {daysRemaining === 1
                      ? t("subscription.daysRemaining", { count: daysRemaining })
                      : t("subscription.daysRemainingPlural", { count: daysRemaining })}
                  </span>
                </div>
              )}

              {/* End date */}
              {isTrial && trialEndsAt && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{t("subscription.expiresOn")}</span>
                  <span className="text-sm font-medium">
                    {new Date(trialEndsAt).toLocaleDateString()}
                  </span>
                </div>
              )}
              {subStatus === "active" && subscriptionEndsAt && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{t("subscription.renewsOn")}</span>
                  <span className="text-sm font-medium">
                    {new Date(subscriptionEndsAt).toLocaleDateString()}
                  </span>
                </div>
              )}

              {/* Subscribe / Manage button */}
              <div className="pt-1 space-y-2">
                {(isTrial || isExpired) ? (
                  <button
                    type="button"
                    onClick={handleSubscribeClick}
                    disabled={checkoutLoading}
                    className="h-10 w-full rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                  >
                    {checkoutLoading
                      ? t("subscription.redirecting", "Redirecting to checkout…")
                      : isExpired
                        ? t("subscription.resubscribe", "Resubscribe")
                        : t("subscription.upgradeNow", "Upgrade to Pro")}
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled
                    title={t("subscription.comingSoon")}
                    className="h-10 w-full rounded-md border border-border bg-muted px-4 text-sm font-medium text-muted-foreground disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {t("subscription.managePlan")} — {t("subscription.comingSoon")}
                  </button>
                )}
                {checkoutError && (
                  <p className="text-xs text-destructive">{checkoutError}</p>
                )}
              </div>
            </div>
          )}
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
              {signingOut ? t("settings.signingOut", { defaultValue: "Signing out..." }) : t("settings.signOut")}
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
