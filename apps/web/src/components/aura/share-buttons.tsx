"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Link2, Check, Download, Send } from "lucide-react";

interface ShareButtonsProps {
  username: string;
  overallScore: number;
  badgeTier: string;
}

export function ShareButtons({ username, overallScore, badgeTier }: ShareButtonsProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

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
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available — fallback ignored
    }
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
        Telegram
      </Button>

      <Button variant="outline" size="sm" onClick={openLinkedIn} className="gap-1.5">
        LinkedIn
      </Button>

      <Button variant="outline" size="sm" onClick={openWhatsApp} className="gap-1.5">
        WhatsApp
      </Button>

      <Button size="sm" onClick={downloadCard} className="gap-1.5">
        <Download className="size-3.5" aria-hidden="true" />
        {t("aura.downloadCard")}
      </Button>
    </div>
  );
}
