"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { QrCode, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "@/hooks/queries/use-auth-token";
import { TopBar } from "@/components/layout/top-bar";
import { useEnergyMode } from "@/hooks/use-energy-mode";

export default function CheckinPage() {
  const { t } = useTranslation();
  const { eventId } = useParams<{ eventId: string }>();
  const getToken = useAuthToken();

  const { energy } = useEnergyMode();
  const isLow = energy === "low";
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleCheckin() {
    if (!code.trim() || !eventId) return;
    setStatus("loading");
    try {
      const token = await getToken();
      if (!token) {
        setStatus("error");
        setMessage(t("common.notAuthenticated", { defaultValue: "Not authenticated" }));
        return;
      }
      await apiFetch(`/api/events/${eventId}/checkin`, {
        method: "POST",
        body: JSON.stringify({ check_in_code: code.trim() }),
        token,
      });
      setStatus("success");
      setMessage(t("events.checkinSuccess", { defaultValue: "Check-in successful!" }));
      setCode("");
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof ApiError ? e.detail : t("error.generic", { defaultValue: "Something went wrong" }));
    }
  }

  return (
    <>
      <TopBar title={t("events.checkin", { defaultValue: "Event Check-in" })} />
      <div className="max-w-md mx-auto p-4 space-y-6">
        <div className="text-center space-y-2">
          {!isLow && <QrCode className="size-12 text-primary mx-auto" />}
          <h2 className="text-lg font-bold">{t("events.enterCode", { defaultValue: "Enter check-in code" })}</h2>
          {!isLow && (
            <p className="text-sm text-muted-foreground">
              {t("events.checkinDesc", { defaultValue: "Enter the code provided by the event coordinator." })}
            </p>
          )}
        </div>

        <div className="space-y-3">
          <input
            type="text"
            value={code}
            onChange={(e) => { setCode(e.target.value); setStatus("idle"); }}
            placeholder={t("events.codePlaceholder", { defaultValue: "Enter code..." })}
            className="w-full rounded-lg border border-input bg-background px-4 py-3 text-center text-lg font-mono tracking-widest placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            maxLength={20}
            autoFocus
          />
          <Button
            onClick={handleCheckin}
            disabled={!code.trim() || status === "loading"}
            className="w-full gap-2"
            size="lg"
          >
            {status === "loading" ? (
              <><Loader2 className="size-4 animate-spin" aria-hidden="true" /> {t("common.loading", { defaultValue: "..." })}</>
            ) : (
              <><QrCode className="size-4" /> {t("events.checkinButton", { defaultValue: "Check In" })}</>
            )}
          </Button>
        </div>

        {status === "success" && (
          <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 text-emerald-400">
            <CheckCircle className="size-5 shrink-0" />
            <span className="text-sm font-medium">{message}</span>
          </div>
        )}

        {status === "error" && (
          <div className="flex items-center gap-2 rounded-lg bg-purple-500/10 border border-purple-500/20 p-3 text-purple-400">
            <XCircle className="size-5 shrink-0" />
            <span className="text-sm font-medium">{message}</span>
          </div>
        )}
      </div>
    </>
  );
}
