"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Link2, Check, Download, Send, Share2 } from "lucide-react";

interface ShareButtonsProps {
  username: string;
  overallScore: number;
  badgeTier: string;
}

export function ShareButtons({ username, overallScore, badgeTier }: ShareButtonsProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [tiktokCopied, setTiktokCopied] = useState(false);

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

  function downloadCard() {
    const cardUrl = `/u/${username}/card?format=linkedin`;
    window.open(cardUrl, "_blank", "noopener");
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={copyLink}
        className="gap-1.5"
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

      <Button variant="outline" size="sm" onClick={openTelegram} className="gap-1.5">
        <Send className="size-3.5" aria-hidden="true" />
        {t("aura.telegram")}
      </Button>

      <Button variant="outline" size="sm" onClick={openLinkedIn} className="gap-1.5">
        {t("aura.linkedin")}
      </Button>

      <Button variant="outline" size="sm" onClick={openWhatsApp} className="gap-1.5">
        {t("aura.whatsapp")}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={openTikTok}
        className="gap-1.5"
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

      {/* Download Card — backend route not yet implemented; shown as coming soon */}
      <Button
        size="sm"
        disabled
        title={t("aura.downloadCardSoon", { defaultValue: "Card download coming soon" })}
        className="gap-1.5 opacity-50 cursor-not-allowed"
        aria-disabled="true"
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
