"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Link2, Check, Download, Send, Share2 } from "lucide-react";

interface ShareButtonsProps {
  username: string | null | undefined;
  overallScore: number;
  badgeTier: string;
  /** URL to the settings page — passed by parent so this component stays locale-unaware */
  settingsUrl?: string;
}

export function ShareButtons({ username, overallScore, badgeTier, settingsUrl }: ShareButtonsProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [tiktokCopied, setTiktokCopied] = useState(false);

  // BUG-GROWTH-8 FIX: Guard includes direct link to Settings — no dead end for users without username
  if (!username) {
    return (
      <p className="text-sm text-muted-foreground">
        {t("aura.setUsernameToShare", {
          defaultValue: "Set a username in Settings to unlock sharing.",
        })}{" "}
        {settingsUrl && (
          <a href={settingsUrl} className="text-primary hover:underline font-medium">
            {t("aura.goToSettings", { defaultValue: "Go to Settings →" })}
          </a>
        )}
      </p>
    );
  }

  const profileUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/u/${username}?utm_source=share&utm_medium=volaura`
      : `/u/${username}`;

  const tierLabel = t(`aura.${badgeTier}`, { defaultValue: badgeTier });
  const shareText = t("aura.shareText", {
    score: overallScore.toFixed(0),
    badge: tierLabel,
  }) + ` ${profileUrl}`;

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(profileUrl);
    } catch {
      // Clipboard API blocked (non-HTTPS, permissions) — use execCommand fallback
      try {
        const el = document.createElement("textarea");
        el.value = profileUrl;
        el.style.position = "fixed";
        el.style.opacity = "0";
        document.body.appendChild(el);
        el.focus();
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);
      } catch {
        // Both methods failed — user sees feedback anyway (optimistic UX)
      }
    }
    // Always show feedback — never silent fail
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function openTelegram() {
    window.open(
      `https://t.me/share/url?url=${encodeURIComponent(profileUrl)}&text=${encodeURIComponent(shareText)}`,
      "_blank",
      "noopener"
    );
  }

  function openLinkedIn() {
    window.open(
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(profileUrl)}`,
      "_blank",
      "noopener"
    );
  }

  function openWhatsApp() {
    window.open(
      `https://wa.me/?text=${encodeURIComponent(shareText)}`,
      "_blank",
      "noopener"
    );
  }

  async function openTikTok() {
    // TikTok has no direct share API — copy caption to clipboard, user pastes in video caption
    const caption = `${tierLabel} badge on Volaura! 🏅 Score: ${overallScore.toFixed(0)} ${profileUrl} #Volaura #${badgeTier}`;
    try {
      await navigator.clipboard.writeText(caption);
    } catch {
      // Fallback already shows feedback
    }
    // Show "caption copied" feedback before opening TikTok
    setTiktokCopied(true);
    setTimeout(() => setTiktokCopied(false), 2500);
    window.open("https://www.tiktok.com/upload", "_blank", "noopener");
  }

  async function nativeShare() {
    try {
      await navigator.share({
        title: `${tierLabel} Badge — Volaura`,
        text: shareText,
        url: profileUrl,
      });
    } catch {
      // User cancelled or share not supported
    }
  }

  async function downloadCard() {
    try {
      const cardUrl = `/u/${username}/card?format=linkedin`;
      const res = await fetch(cardUrl);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `volaura-${username}-${badgeTier}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // Fallback: open in new tab
      window.open(`/u/${username}/card?format=linkedin`, "_blank", "noopener");
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={copyLink}
        className="gap-1.5 min-h-[44px] sm:min-h-0"
      >
        {copied ? (
          <>
            <Check className="size-3.5" aria-hidden="true" />
            {t("aura.copied")}
          </>
        ) : (
          <>
            <Link2 className="size-3.5" aria-hidden="true" />
            {t("aura.copyLink")}
          </>
        )}
      </Button>

      <Button variant="outline" size="sm" onClick={openTelegram} className="gap-1.5 min-h-[44px] sm:min-h-0" aria-label={t("aura.telegram") + " (opens in new window)"}>
        <Send className="size-3.5" aria-hidden="true" />
        {t("aura.telegram")}
      </Button>

      <Button variant="outline" size="sm" onClick={openLinkedIn} className="gap-1.5 min-h-[44px] sm:min-h-0" aria-label={t("aura.linkedin") + " (opens in new window)"}>
        {t("aura.linkedin")}
      </Button>

      <Button variant="outline" size="sm" onClick={openWhatsApp} className="gap-1.5 min-h-[44px] sm:min-h-0" aria-label={t("aura.whatsapp") + " (opens in new window)"}>
        {t("aura.whatsapp")}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={openTikTok}
        className="gap-1.5 min-h-[44px] sm:min-h-0"
        aria-label={tiktokCopied ? t("aura.captionCopied", { defaultValue: "Caption copied!" }) : t("aura.tiktok") + " (opens in new window)"}
      >
        {tiktokCopied ? (
          <>
            <Check className="size-3.5" aria-hidden="true" />
            {t("aura.captionCopied", { defaultValue: "Caption copied!" })}
          </>
        ) : (
          t("aura.tiktok")
        )}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={downloadCard}
        className="gap-1.5 min-h-[44px] sm:min-h-0"
      >
        <Download className="size-3.5" aria-hidden="true" />
        {t("aura.downloadCard")}
      </Button>

      {typeof navigator !== "undefined" && "share" in navigator && (
        <Button variant="outline" size="sm" onClick={nativeShare} className="gap-1.5">
          <Share2 className="size-3.5" aria-hidden="true" />
          {t("aura.share", { defaultValue: "More" })}
        </Button>
      )}
    </div>
  );
}
