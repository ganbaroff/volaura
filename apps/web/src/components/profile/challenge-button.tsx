"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Share2 } from "lucide-react";

interface ChallengeButtonProps {
  username: string;
}

export function ChallengeButton({ username }: ChallengeButtonProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  function handleClick() {
    const url = `https://volaura.app/?ref=${username}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 min-h-[44px] text-sm font-medium hover:bg-muted transition-colors"
    >
      <Share2 className="h-4 w-4 shrink-0" aria-hidden="true" />
      {copied ? t("profile.challengeLink") : t("profile.challengePeer")}
    </button>
  );
}
