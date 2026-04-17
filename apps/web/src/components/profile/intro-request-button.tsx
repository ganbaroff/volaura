"use client";

import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useFocusTrap } from "@/hooks/use-focus-trap";
import { useMyOrganization, useCreateIntroRequest } from "@/hooks/queries/use-organizations";
import type { ApiError } from "@/lib/api/client";

interface Props {
  professionalId: string;
  professionalName: string;
}

type Timeline = "urgent" | "normal" | "flexible";

export function IntroRequestButton({ professionalId, professionalName }: Props) {
  const { t } = useTranslation();
  const { data: org } = useMyOrganization();
  const mutation = useCreateIntroRequest();

  const [open, setOpen] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [timeline, setTimeline] = useState<Timeline>("normal");
  const [message, setMessage] = useState("");
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const dialogRef = useFocusTrap<HTMLDivElement>(open);
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  // Only render for org users (those who have an org record)
  if (!org) return null;

  function handleClose() {
    setOpen(false);
    setProjectName("");
    setTimeline("normal");
    setMessage("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!projectName.trim()) return;

    mutation.mutate(
      { professional_id: professionalId, project_name: projectName.trim(), timeline, message: message.trim() || undefined },
      {
        onSuccess: () => {
          if (!isMounted.current) return;
          handleClose();
          setToast({ type: "success", msg: t("intro.sent", { defaultValue: "Introduction request sent!" }) });
          setTimeout(() => { if (isMounted.current) setToast(null); }, 4000);
        },
        onError: (err: unknown) => {
          if (!isMounted.current) return;
          const apiErr = err as ApiError;
          const msg =
            apiErr?.status === 409
              ? t("intro.alreadySent", { defaultValue: "You already sent a request to this professional." })
              : t("intro.error", { defaultValue: "Failed to send request. Please try again." });
          setToast({ type: "error", msg });
          setTimeout(() => { if (isMounted.current) setToast(null); }, 5000);
        },
      },
    );
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="w-full rounded-xl bg-primary px-6 py-3 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        {t("intro.button", { defaultValue: "Request Introduction" })}
      </button>

      {/* Toast */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 rounded-xl px-5 py-3 text-sm font-medium shadow-lg ${
            toast.type === "success"
              ? "bg-emerald-600 text-white"
              : "bg-destructive text-destructive-foreground"
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Modal backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm p-4"
          onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
        >
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="intro-modal-title"
            className="w-full max-w-md rounded-2xl border border-border bg-surface-container p-6 space-y-5 shadow-xl"
          >
            <div>
              <h2 id="intro-modal-title" className="text-lg font-bold text-on-surface">
                {t("intro.modalTitle", { defaultValue: "Request Introduction" })}
              </h2>
              <p className="mt-1 text-sm text-on-surface-variant">
                {t("intro.modalSubtitle", {
                  name: professionalName,
                  defaultValue: `Send a project intro to ${professionalName}`,
                })}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Project name */}
              <div className="space-y-1.5">
                <label htmlFor="intro-project" className="text-sm font-medium text-on-surface">
                  {t("intro.projectName", { defaultValue: "Project name" })}
                  <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
                </label>
                <input
                  id="intro-project"
                  type="text"
                  required
                  maxLength={200}
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder={t("intro.projectPlaceholder", { defaultValue: "e.g. COP30 Youth Leadership Programme" })}
                  className="w-full rounded-xl border border-outline-variant bg-surface px-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>

              {/* Timeline */}
              <div className="space-y-1.5">
                <label htmlFor="intro-timeline" className="text-sm font-medium text-on-surface">
                  {t("intro.timeline", { defaultValue: "Timeline" })}
                </label>
                <select
                  id="intro-timeline"
                  value={timeline}
                  onChange={(e) => setTimeline(e.target.value as Timeline)}
                  className="w-full rounded-xl border border-outline-variant bg-surface px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40"
                >
                  <option value="urgent">{t("intro.timelineUrgent", { defaultValue: "Urgent (within 1 week)" })}</option>
                  <option value="normal">{t("intro.timelineNormal", { defaultValue: "Normal (2–4 weeks)" })}</option>
                  <option value="flexible">{t("intro.timelineFlexible", { defaultValue: "Flexible (1–3 months)" })}</option>
                </select>
              </div>

              {/* Message (optional) */}
              <div className="space-y-1.5">
                <label htmlFor="intro-message" className="text-sm font-medium text-on-surface">
                  {t("intro.message", { defaultValue: "Message" })}
                  <span className="ml-1 text-xs text-on-surface-variant">
                    {t("intro.optional", { defaultValue: "(optional)" })}
                  </span>
                </label>
                <textarea
                  id="intro-message"
                  maxLength={500}
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder={t("intro.messagePlaceholder", { defaultValue: "Why are you reaching out?" })}
                  className="w-full resize-none rounded-xl border border-outline-variant bg-surface px-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
                <p className="text-xs text-on-surface-variant text-right">{message.length}/500</p>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 rounded-xl border border-outline-variant px-4 py-2.5 text-sm font-medium text-on-surface hover:bg-surface-container-high transition-colors"
                >
                  {t("common.cancel", { defaultValue: "Cancel" })}
                </button>
                <button
                  type="submit"
                  disabled={mutation.isPending || !projectName.trim()}
                  className="flex-1 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {mutation.isPending
                    ? t("intro.sending", { defaultValue: "Sending…" })
                    : t("intro.send", { defaultValue: "Send Request" })}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
